# vision_ocr.py
# Install: pip install pyobjc-framework-Vision pyobjc-framework-Quartz
import sys
import json
import Quartz
import Vision
from Cocoa import NSURL


def apple_vision_ocr(image_path):
    input_url = NSURL.fileURLWithPath_(image_path)
    image_source = Quartz.CGImageSourceCreateWithURL(input_url, None)
    image = Quartz.CGImageSourceCreateImageAtIndex(image_source, 0, None)

    img_width = Quartz.CGImageGetWidth(image)
    img_height = Quartz.CGImageGetHeight(image)

    results = []

    def handler(request, error):
        if error:
            print(f"Error: {error}", file=sys.stderr)
            return
        for obs in request.results():
            top = obs.topCandidates_(1)[0]
            bbox = obs.boundingBox()  # normalized, origin BOTTOM-left

            # convert to pixel coords, origin TOP-left, matching our
            # existing [x1, y1, x2, y2] convention from the PaddleOCR work
            x1 = bbox.origin.x * img_width
            x2 = x1 + bbox.size.width * img_width
            y2 = img_height - (bbox.origin.y * img_height)
            y1 = y2 - bbox.size.height * img_height

            results.append({
                "text": top.string(),
                "score": top.confidence(),
                "box": [x1, y1, x2, y2],
            })

    request = Vision.VNRecognizeTextRequest.alloc().initWithCompletionHandler_(handler)
    request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
    request.setUsesLanguageCorrection_(True)

    handler_instance = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(image, None)
    success, error = handler_instance.performRequests_error_([request], None)

    if not success:
        print(f"OCR Failed: {error}", file=sys.stderr)
        return None

    # NOTE: this is Vision's own default ordering (its internal reading-order
    # heuristic), NOT re-sorted by us. That's deliberate -- we want to see
    # and validate what Vision decided, same way we validated PPStructureV3's
    # block_order rather than blindly trusting it.
    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python vision_ocr.py <image_path>")
        sys.exit(1)
    results = apple_vision_ocr(sys.argv[1])
    if results is not None:
        print(json.dumps(results, indent=2))