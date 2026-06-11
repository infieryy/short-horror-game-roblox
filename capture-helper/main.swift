// blender-capture: ScreenCaptureKit window capture -> VideoToolbox H.264 -> stdout
//
// Captures a single macOS window (desktop-independent, works while occluded),
// hardware-encodes it with VideoToolbox (Apple Silicon), and writes Annex B
// H.264 frames to stdout using a simple length-prefixed framing:
//
//   [u32 BE payload_len][u8 flags (bit0 = keyframe)][u64 BE pts_microseconds][payload]
//
// stdin accepts line commands:
//   keyframe   -> force the next encoded frame to be an IDR keyframe
//
// Usage:
//   blender-capture --window-id <id> --width <px> --height <px> [--fps 60] [--bitrate 8000000]
//
// Requires macOS 13+ (Sonoma recommended). Screen Recording permission must be
// granted to the process that spawns this helper (e.g. Terminal).

import AVFoundation
import CoreGraphics
import CoreMedia
import Foundation
import ScreenCaptureKit
import VideoToolbox

// MARK: - Argument parsing

func parseArgs() -> (windowID: UInt32, width: Int, height: Int, fps: Int, bitrate: Int) {
    var windowID: UInt32 = 0
    var width = 1280
    var height = 720
    var fps = 60
    var bitrate = 8_000_000

    var args = Array(CommandLine.arguments.dropFirst())
    while !args.isEmpty {
        let flag = args.removeFirst()
        guard !args.isEmpty else { break }
        let value = args.removeFirst()
        switch flag {
        case "--window-id": windowID = UInt32(value) ?? 0
        case "--width": width = Int(value) ?? width
        case "--height": height = Int(value) ?? height
        case "--fps": fps = Int(value) ?? fps
        case "--bitrate": bitrate = Int(value) ?? bitrate
        default: break
        }
    }
    if windowID == 0 {
        FileHandle.standardError.write("error: --window-id is required\n".data(using: .utf8)!)
        exit(2)
    }
    // Encoders want even dimensions.
    width -= width % 2
    height -= height % 2
    return (windowID, width, height, fps, bitrate)
}

let params = parseArgs()

// MARK: - Frame writer (stdout)

final class FrameWriter {
    private let handle = FileHandle.standardOutput
    private let queue = DispatchQueue(label: "frame-writer")

    func write(payload: Data, keyframe: Bool, ptsMicros: UInt64) {
        var header = Data(capacity: 13)
        var len = UInt32(payload.count).bigEndian
        withUnsafeBytes(of: &len) { header.append(contentsOf: $0) }
        header.append(keyframe ? 1 : 0)
        var pts = ptsMicros.bigEndian
        withUnsafeBytes(of: &pts) { header.append(contentsOf: $0) }
        queue.sync {
            do {
                try handle.write(contentsOf: header)
                try handle.write(contentsOf: payload)
            } catch {
                // Downstream pipe closed: the session manager went away. Exit.
                exit(0)
            }
        }
    }
}

// MARK: - H.264 encoder (VideoToolbox)

final class H264Encoder {
    private var session: VTCompressionSession?
    private let writer: FrameWriter
    private let fps: Int
    var forceNextKeyframe = false

    init(width: Int, height: Int, fps: Int, bitrate: Int, writer: FrameWriter) {
        self.writer = writer
        self.fps = fps

        var s: VTCompressionSession?
        let status = VTCompressionSessionCreate(
            allocator: kCFAllocatorDefault,
            width: Int32(width),
            height: Int32(height),
            codecType: kCMVideoCodecType_H264,
            encoderSpecification: nil,
            imageBufferAttributes: nil,
            compressedDataAllocator: nil,
            outputCallback: nil,
            refcon: nil,
            compressionSessionOut: &s
        )
        guard status == noErr, let session = s else {
            FileHandle.standardError.write("error: VTCompressionSessionCreate failed (\(status))\n".data(using: .utf8)!)
            exit(1)
        }

        // Low-latency realtime configuration: no B-frames, frequent-enough IDRs.
        VTSessionSetProperty(session, key: kVTCompressionPropertyKey_RealTime, value: kCFBooleanTrue)
        VTSessionSetProperty(session, key: kVTCompressionPropertyKey_AllowFrameReordering, value: kCFBooleanFalse)
        VTSessionSetProperty(session, key: kVTCompressionPropertyKey_ProfileLevel, value: kVTProfileLevel_H264_Main_AutoLevel)
        VTSessionSetProperty(session, key: kVTCompressionPropertyKey_AverageBitRate, value: bitrate as CFNumber)
        VTSessionSetProperty(session, key: kVTCompressionPropertyKey_ExpectedFrameRate, value: fps as CFNumber)
        VTSessionSetProperty(session, key: kVTCompressionPropertyKey_MaxKeyFrameInterval, value: (fps * 2) as CFNumber)
        VTSessionSetProperty(session, key: kVTCompressionPropertyKey_MaxKeyFrameIntervalDuration, value: 2 as CFNumber)
        // Prefer low-latency rate control when available (Apple Silicon).
        VTSessionSetProperty(session, key: kVTVideoEncoderSpecification_EnableLowLatencyRateControl, value: kCFBooleanTrue)
        VTCompressionSessionPrepareToEncodeFrames(session)
        self.session = session
    }

    func encode(pixelBuffer: CVPixelBuffer, pts: CMTime) {
        guard let session = session else { return }
        var frameProperties: CFDictionary?
        if forceNextKeyframe {
            forceNextKeyframe = false
            frameProperties = [kVTEncodeFrameOptionKey_ForceKeyFrame: kCFBooleanTrue!] as CFDictionary
        }
        let duration = CMTime(value: 1, timescale: CMTimeScale(fps))
        VTCompressionSessionEncodeFrame(
            session,
            imageBuffer: pixelBuffer,
            presentationTimeStamp: pts,
            duration: duration,
            frameProperties: frameProperties,
            infoFlagsOut: nil
        ) { [weak self] status, _, sampleBuffer in
            guard status == noErr, let sampleBuffer = sampleBuffer, let self = self else { return }
            self.emit(sampleBuffer: sampleBuffer)
        }
    }

    private func emit(sampleBuffer: CMSampleBuffer) {
        guard let dataBuffer = CMSampleBufferGetDataBuffer(sampleBuffer) else { return }

        var isKeyframe = true
        if let attachments = CMSampleBufferGetSampleAttachmentsArray(sampleBuffer, createIfNecessary: false) as? [[CFString: Any]],
           let first = attachments.first,
           let notSync = first[kCMSampleAttachmentKey_NotSync] as? Bool {
            isKeyframe = !notSync
        }

        var out = Data()
        let startCode: [UInt8] = [0, 0, 0, 1]

        // Prepend SPS/PPS in-band on keyframes so the WebCodecs decoder can
        // configure itself from the Annex B stream alone (no avcC description).
        if isKeyframe, let format = CMSampleBufferGetFormatDescription(sampleBuffer) {
            var parameterSetCount = 0
            CMVideoFormatDescriptionGetH264ParameterSetAtIndex(
                format, parameterSetIndex: 0,
                parameterSetPointerOut: nil, parameterSetSizeOut: nil,
                parameterSetCountOut: &parameterSetCount, nalUnitHeaderLengthOut: nil
            )
            for i in 0..<parameterSetCount {
                var ptr: UnsafePointer<UInt8>?
                var size = 0
                let st = CMVideoFormatDescriptionGetH264ParameterSetAtIndex(
                    format, parameterSetIndex: i,
                    parameterSetPointerOut: &ptr, parameterSetSizeOut: &size,
                    parameterSetCountOut: nil, nalUnitHeaderLengthOut: nil
                )
                if st == noErr, let p = ptr {
                    out.append(contentsOf: startCode)
                    out.append(p, count: size)
                }
            }
        }

        // Convert AVCC (length-prefixed) NAL units to Annex B (start codes).
        var totalLength = 0
        var dataPointer: UnsafeMutablePointer<CChar>?
        guard CMBlockBufferGetDataPointer(
            dataBuffer, atOffset: 0, lengthAtOffsetOut: nil,
            totalLengthOut: &totalLength, dataPointerOut: &dataPointer
        ) == noErr, let base = dataPointer else { return }

        var offset = 0
        while offset + 4 <= totalLength {
            var nalLength: UInt32 = 0
            memcpy(&nalLength, base + offset, 4)
            nalLength = UInt32(bigEndian: nalLength)
            let end = offset + 4 + Int(nalLength)
            if end > totalLength { break }
            out.append(contentsOf: startCode)
            base.withMemoryRebound(to: UInt8.self, capacity: totalLength) { u8 in
                out.append(u8 + offset + 4, count: Int(nalLength))
            }
            offset = end
        }

        let pts = CMSampleBufferGetPresentationTimeStamp(sampleBuffer)
        let ptsMicros = UInt64(max(0, pts.seconds) * 1_000_000)
        writer.write(payload: out, keyframe: isKeyframe, ptsMicros: ptsMicros)
    }
}

// MARK: - Stream output

final class CaptureOutput: NSObject, SCStreamOutput, SCStreamDelegate {
    let encoder: H264Encoder

    init(encoder: H264Encoder) {
        self.encoder = encoder
    }

    func stream(_ stream: SCStream, didOutputSampleBuffer sampleBuffer: CMSampleBuffer, of type: SCStreamOutputType) {
        guard type == .screen, sampleBuffer.isValid else { return }
        // Skip incomplete frames (e.g. window not yet ready).
        guard let attachments = CMSampleBufferGetSampleAttachmentsArray(sampleBuffer, createIfNecessary: false) as? [[SCStreamFrameInfo: Any]],
              let first = attachments.first,
              let statusRaw = first[.status] as? Int,
              let status = SCFrameStatus(rawValue: statusRaw),
              status == .complete else { return }
        guard let pixelBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) else { return }
        encoder.encode(pixelBuffer: pixelBuffer, pts: CMSampleBufferGetPresentationTimeStamp(sampleBuffer))
    }

    func stream(_ stream: SCStream, didStopWithError error: Error) {
        FileHandle.standardError.write("stream stopped: \(error.localizedDescription)\n".data(using: .utf8)!)
        exit(1)
    }
}

// MARK: - stdin command listener

func startStdinListener(encoder: H264Encoder) {
    Thread {
        while let line = readLine(strippingNewline: true) {
            switch line.trimmingCharacters(in: .whitespaces) {
            case "keyframe":
                encoder.forceNextKeyframe = true
            case "quit":
                exit(0)
            default:
                break
            }
        }
        // stdin closed -> parent is gone.
        exit(0)
    }.start()
}

// MARK: - Main

let writer = FrameWriter()
let encoder = H264Encoder(width: params.width, height: params.height, fps: params.fps, bitrate: params.bitrate, writer: writer)
let output = CaptureOutput(encoder: encoder)
startStdinListener(encoder: encoder)

Task {
    do {
        let content = try await SCShareableContent.excludingDesktopWindows(false, onScreenWindowsOnly: false)
        guard let window = content.windows.first(where: { $0.windowID == CGWindowID(params.windowID) }) else {
            FileHandle.standardError.write("error: window \(params.windowID) not found\n".data(using: .utf8)!)
            exit(3)
        }

        let filter = SCContentFilter(desktopIndependentWindow: window)
        let config = SCStreamConfiguration()
        config.width = params.width
        config.height = params.height
        config.minimumFrameInterval = CMTime(value: 1, timescale: CMTimeScale(params.fps))
        config.pixelFormat = kCVPixelFormatType_32BGRA
        config.showsCursor = false
        config.queueDepth = 5

        let stream = SCStream(filter: filter, configuration: config, delegate: output)
        try stream.addStreamOutput(output, type: .screen, sampleHandlerQueue: DispatchQueue(label: "capture"))
        try await stream.startCapture()
        FileHandle.standardError.write("capture started: window=\(params.windowID) \(params.width)x\(params.height)@\(params.fps)\n".data(using: .utf8)!)
    } catch {
        FileHandle.standardError.write("error: failed to start capture: \(error.localizedDescription)\n".data(using: .utf8)!)
        exit(1)
    }
}

RunLoop.main.run()
