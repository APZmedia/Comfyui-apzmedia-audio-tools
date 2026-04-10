import json
import numpy as np
import torch
from scipy import signal


class AudioEqualizer:
    """Parametric EQ with visual curve editor - DaVinci Resolve style."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "audio": ("AUDIO",),
                "eq_bands_json": ("STRING", {
                    "default": '[{"freq": 100, "gain": 0, "q": 0.71, "type": "low_shelf"}, {"freq": 1000, "gain": 0, "q": 1.0, "type": "peak"}, {"freq": 10000, "gain": 0, "q": 0.71, "type": "high_shelf"}]',
                    "multiline": True,
                }),
            },
            "optional": {
                "selected_band": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 5,
                    "step": 1,
                    "tooltip": "Select which band to edit (0-5)",
                }),
                "band_frequency": ("FLOAT", {
                    "default": 1000.0,
                    "min": 20.0,
                    "max": 20000.0,
                    "step": 1.0,
                    "tooltip": "Center frequency in Hz",
                }),
                "band_gain": ("FLOAT", {
                    "default": 0.0,
                    "min": -24.0,
                    "max": 24.0,
                    "step": 0.1,
                    "tooltip": "Gain in dB",
                }),
                "band_q": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.1,
                    "max": 10.0,
                    "step": 0.01,
                    "tooltip": "Q factor (bandwidth)",
                }),
                "band_type": (["peak", "low_shelf", "high_shelf", "low_pass", "high_pass"], {
                    "tooltip": "Filter type",
                }),
                "master_gain_db": ("FLOAT", {
                    "default": 0.0,
                    "min": -24.0,
                    "max": 24.0,
                    "step": 0.1,
                    "tooltip": "Master output gain",
                }),
            }
        }

    RETURN_TYPES = ("AUDIO",)
    RETURN_NAMES = ("audio",)
    FUNCTION = "apply_eq"
    CATEGORY = "APZmedia/Audio"

    FILTER_TYPES = ["peak", "low_shelf", "high_shelf", "low_pass", "high_pass"]

    def db_to_linear(self, db):
        """Convert dB to linear gain."""
        return 10 ** (db / 20.0)

    def linear_to_db(self, linear):
        """Convert linear gain to dB."""
        return 20.0 * np.log10(max(abs(linear), 1e-10))

    def calculate_biquad_coeffs(self, sample_rate, filter_type, freq, gain_db, q):
        """
        Calculate biquad filter coefficients using standard formulas.
        Returns b0, b1, b2, a0, a1, a2 (normalized so a0=1)
        """
        A = 10 ** (gain_db / 40.0)  # For shelving filters
        sqrt_A = np.sqrt(A)
        omega = 2.0 * np.pi * freq / sample_rate
        sn = np.sin(omega)
        cs = np.cos(omega)
        alpha = sn / (2.0 * q)

        if filter_type == "peak":
            # Peaking EQ
            b0 = 1.0 + alpha * A
            b1 = -2.0 * cs
            b2 = 1.0 - alpha * A
            a0 = 1.0 + alpha / A
            a1 = -2.0 * cs
            a2 = 1.0 - alpha / A

        elif filter_type == "low_shelf":
            # Low shelving filter
            b0 = A * ((A + 1) - (A - 1) * cs + 2 * sqrt_A * alpha)
            b1 = 2 * A * ((A - 1) - (A + 1) * cs)
            b2 = A * ((A + 1) - (A - 1) * cs - 2 * sqrt_A * alpha)
            a0 = (A + 1) + (A - 1) * cs + 2 * sqrt_A * alpha
            a1 = -2 * ((A - 1) + (A + 1) * cs)
            a2 = (A + 1) + (A - 1) * cs - 2 * sqrt_A * alpha

        elif filter_type == "high_shelf":
            # High shelving filter
            b0 = A * ((A + 1) + (A - 1) * cs + 2 * sqrt_A * alpha)
            b1 = -2 * A * ((A - 1) + (A + 1) * cs)
            b2 = A * ((A + 1) + (A - 1) * cs - 2 * sqrt_A * alpha)
            a0 = (A + 1) - (A - 1) * cs + 2 * sqrt_A * alpha
            a1 = 2 * ((A - 1) - (A + 1) * cs)
            a2 = (A + 1) - (A - 1) * cs - 2 * sqrt_A * alpha

        elif filter_type == "low_pass":
            # 12dB/octave low pass (second order)
            b0 = (1.0 - cs) / 2.0
            b1 = 1.0 - cs
            b2 = (1.0 - cs) / 2.0
            a0 = 1.0 + alpha
            a1 = -2.0 * cs
            a2 = 1.0 - alpha

        elif filter_type == "high_pass":
            # 12dB/octave high pass (second order)
            b0 = (1.0 + cs) / 2.0
            b1 = -(1.0 + cs)
            b2 = (1.0 + cs) / 2.0
            a0 = 1.0 + alpha
            a1 = -2.0 * cs
            a2 = 1.0 - alpha

        else:
            # Default to bypass (all-pass)
            b0, b1, b2 = 1.0, 0.0, 0.0
            a0, a1, a2 = 1.0, 0.0, 0.0

        # Normalize coefficients
        b0 /= a0
        b1 /= a0
        b2 /= a0
        a1 /= a0
        a2 /= a0

        return [b0, b1, b2, 1.0, a1, a2]

    def apply_sos_filter(self, audio_data, sos_coeffs):
        """Apply second-order sections filter to audio."""
        return signal.sosfilt(sos_coeffs, audio_data)

    def calculate_frequency_response(self, sample_rate, eq_bands, num_points=512):
        """
        Calculate the combined frequency response of all EQ bands.
        Returns frequencies (Hz) and gains (dB).
        """
        frequencies = np.logspace(np.log10(20), np.log10(20000), num_points)
        total_response = np.zeros(num_points)

        for band in eq_bands:
            freq = float(band.get("freq", 1000))
            gain_db = float(band.get("gain", 0))
            q = float(band.get("q", 1.0))
            filter_type = band.get("type", "peak")

            # Skip bands with 0 gain on shelf/peak filters
            if gain_db == 0 and filter_type in ["peak", "low_shelf", "high_shelf"]:
                continue

            # Calculate band response
            coeffs = self.calculate_biquad_coeffs(sample_rate, filter_type, freq, gain_db, q)
            sos = signal.tf2sos([coeffs[0], coeffs[1], coeffs[2]], [coeffs[3], coeffs[4], coeffs[5]])
            w, h = signal.sosfreqz(sos, frequencies, fs=sample_rate)
            band_response = 20 * np.log10(np.abs(h) + 1e-15)
            total_response += band_response

        return frequencies.tolist(), total_response.tolist()

    def apply_eq(self, audio, eq_bands_json, selected_band=0, band_frequency=1000.0,
                 band_gain=0.0, band_q=1.0, band_type="peak", master_gain_db=0.0):
        """Apply parametric EQ to audio based on JSON band configuration."""
        waveform = audio["waveform"]
        sample_rate = audio["sample_rate"]

        # Parse EQ bands
        try:
            eq_bands = json.loads(eq_bands_json)
            if not isinstance(eq_bands, list):
                eq_bands = []
        except json.JSONDecodeError:
            eq_bands = []

        # Convert to numpy for processing
        waveform_np = waveform.cpu().numpy()
        original_shape = waveform_np.shape

        # Handle mono/stereo (batch, channels, samples)
        is_batch = len(original_shape) == 3
        if is_batch:
            batch_size, num_channels, num_samples = original_shape
            waveform_np = waveform_np.reshape(-1, num_samples)
        else:
            num_channels, num_samples = original_shape
            batch_size = 1

        # Process each channel
        processed = np.zeros_like(waveform_np)

        for ch in range(waveform_np.shape[0]):
            channel_data = waveform_np[ch].copy()

            # Apply each EQ band in series (cascade)
            for band in eq_bands:
                freq = float(band.get("freq", 1000))
                gain_db = float(band.get("gain", 0))
                q = float(band.get("q", 1.0))
                filter_type = band.get("type", "peak")

                # Skip bands that do nothing
                if gain_db == 0 and filter_type in ["peak", "low_shelf", "high_shelf"]:
                    continue

                # Calculate and apply filter
                coeffs = self.calculate_biquad_coeffs(
                    sample_rate, filter_type, freq, gain_db, q
                )
                sos = signal.tf2sos(
                    [coeffs[0], coeffs[1], coeffs[2]],
                    [coeffs[3], coeffs[4], coeffs[5]]
                )
                channel_data = signal.sosfilt(sos, channel_data)

            processed[ch] = channel_data

        # Apply master gain
        if master_gain_db != 0:
            master_linear = self.db_to_linear(master_gain_db)
            processed *= master_linear

        # Restore shape
        if is_batch:
            processed = processed.reshape(original_shape)
        else:
            processed = processed.reshape(num_channels, num_samples)

        # Convert back to tensor
        processed_tensor = torch.from_numpy(processed).float()

        # Ensure we match input format (usually [batch, channels, samples])
        if len(waveform.shape) == 3 and len(processed_tensor.shape) == 2:
            processed_tensor = processed_tensor.unsqueeze(0)

        return ({
            "waveform": processed_tensor,
            "sample_rate": sample_rate,
        },)
