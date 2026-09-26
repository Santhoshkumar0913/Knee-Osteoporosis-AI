import unittest
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from PIL import Image

from app.services.image_model import DINOv2Model
from app.core.config import settings


class DINOv2GradCAMTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service = DINOv2Model()
        image_values = np.zeros((480, 640, 3), dtype=np.uint8)
        image_values[:, :, 0] = np.arange(640, dtype=np.uint8)[None, :]
        image_values[:, :, 1] = np.arange(480, dtype=np.uint8)[:, None]
        image_values[120:360, 180:460, 2] = 220
        cls.image = Image.fromarray(image_values, mode="RGB")

    def test_checkpoint_gradcam_uses_predicted_class_and_expected_map(self):
        prediction = self.service.predict(self.image)
        result = self.service.generate_gradcam(self.image)

        self.assertEqual(result["predicted_class"], prediction["predicted_class"])
        self.assertEqual(result["predicted_diagnosis"], prediction["predicted_diagnosis"])
        self.assertAlmostEqual(result["confidence"], prediction["confidence"], places=6)
        self.assertEqual(
            result["heatmap"].shape,
            (settings.DINOV2_INPUT_SIZE, settings.DINOV2_INPUT_SIZE),
        )
        self.assertEqual(result["heatmap"].dtype, np.float32)
        self.assertTrue(np.isfinite(result["heatmap"]).all())
        self.assertGreater(float(result["heatmap"].max()), 0.0)
        self.assertLessEqual(float(result["heatmap"].max()), 1.0)
        self.assertGreaterEqual(float(result["heatmap"].min()), 0.0)

        target_layer = self.service.model.backbone.blocks[-1].norm1
        self.assertEqual(len(target_layer._forward_hooks), 0)

        # A normal prediction after CAM confirms the temporary hook/gradient
        # path did not change the existing inference result.
        prediction_after_cam = self.service.predict(self.image)
        self.assertEqual(prediction_after_cam, prediction)

    def test_hook_is_removed_when_forward_raises(self):
        target_layer = self.service.model.backbone.blocks[-1].norm1
        original_forward = self.service.model.forward

        def fail_forward(_image_tensor):
            raise RuntimeError("controlled forward failure")

        self.service.model.forward = fail_forward
        try:
            with self.assertRaisesRegex(RuntimeError, "controlled forward failure"):
                self.service.generate_gradcam(self.image)
        finally:
            self.service.model.forward = original_forward

        self.assertEqual(len(target_layer._forward_hooks), 0)

    def test_concurrent_gradcam_requests_serialize_shared_model_forward(self):
        original_forward = self.service.model.forward
        counter_lock = threading.Lock()
        active_forwards = 0
        maximum_active_forwards = 0

        def tracked_forward(image_tensor):
            nonlocal active_forwards, maximum_active_forwards
            with counter_lock:
                active_forwards += 1
                maximum_active_forwards = max(maximum_active_forwards, active_forwards)
            try:
                # Widen the overlap window so missing serialization is observable.
                time.sleep(0.05)
                return original_forward(image_tensor)
            finally:
                with counter_lock:
                    active_forwards -= 1

        self.service.model.forward = tracked_forward
        try:
            with ThreadPoolExecutor(max_workers=2) as executor:
                results = list(executor.map(
                    lambda _request: self.service.generate_gradcam(self.image), range(2)
                ))
        finally:
            self.service.model.forward = original_forward

        self.assertEqual(maximum_active_forwards, 1)
        self.assertEqual(results[0]["predicted_class"], results[1]["predicted_class"])
        self.assertTrue(np.array_equal(results[0]["heatmap"], results[1]["heatmap"]))
        target_layer = self.service.model.backbone.blocks[-1].norm1
        self.assertEqual(len(target_layer._forward_hooks), 0)


if __name__ == "__main__":
    unittest.main()
