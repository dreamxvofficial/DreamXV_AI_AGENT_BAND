import unittest

from backend.services.provider_capabilities import (
    ProviderCapabilityError,
    validate_provider_capability,
)


class TestProviderCapabilities(unittest.TestCase):
    def test_featherless_supports_text(self):
        self.assertEqual(validate_provider_capability("featherless", "text"), "featherless")

    def test_featherless_rejects_images(self):
        with self.assertRaisesRegex(ProviderCapabilityError, "does not support image"):
            validate_provider_capability("featherless", "image")

    def test_aimlapi_supports_text_and_images(self):
        self.assertEqual(validate_provider_capability("aimlapi", "text"), "aimlapi")
        self.assertEqual(validate_provider_capability("aimlapi", "image"), "aimlapi")

    def test_unknown_provider_is_rejected(self):
        with self.assertRaisesRegex(ProviderCapabilityError, "Unknown AI provider"):
            validate_provider_capability("unknown", "image")


if __name__ == "__main__":
    unittest.main()
