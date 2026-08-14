import librosa
import numpy as np
import soundfile as sf
from pathlib import Path
from typing import List, Optional
import time

from app.models import (
    AnalysisResponse,
    AudioAnalysisDetails,
    MediaMetadata,
    ArtifactDetection
)
from app.config import settings


class AudioAnalyzer:
    """
    Analyze audio files for AI-generated content detection
    
    Uses librosa for audio analysis and heuristic methods to detect:
    - Spectral anomalies
    - Pitch inconsistencies
    - Artificial noise patterns
    - Audio artifacts typical of AI generation
    """
    
    def __init__(self):
        self.sample_rate = 22050  # Standard sample rate for analysis
        
    async def analyze(self, file_path: Path) -> AnalysisResponse:
        """
        Analyze audio file for AI-generated content
        
        Args:
            file_path: Path to audio file
            
        Returns:
            AnalysisResponse with analysis results
        """
        # Load audio file
        audio_data, sr = librosa.load(file_path, sr=self.sample_rate)
        
        # Get metadata
        metadata = self._extract_metadata(file_path, audio_data, sr)
        
        # Perform analysis
        spectral_score = self._analyze_spectral_features(audio_data, sr)
        pitch_score = self._analyze_pitch_consistency(audio_data, sr)
        noise_score = self._detect_artificial_noise(audio_data, sr)
        edit_score = self._detect_manual_edits(audio_data, sr)
        
        # Detect artifacts
        artifacts = self._detect_artifacts(audio_data, sr)
        
        # ML deepfake score (optional, improves accuracy)
        ml_score = self._ml_deepfake_score(file_path)
        
        # Combine heuristic and ML scores
        heuristic_score = (spectral_score + pitch_score + noise_score) / 3
        
        if ml_score is not None:
            # Weight: 60% ML, 40% heuristics
            overall_score = (ml_score * 0.6) + (heuristic_score * 0.4)
        else:
            overall_score = heuristic_score
        
        # Determine if AI-generated based on threshold
        is_ai_generated = overall_score >= settings.audio_confidence_threshold
        is_manipulated = (overall_score >= 0.5) or (edit_score >= 0.6)
        
        # Build response
        audio_details = AudioAnalysisDetails(
            spectral_score=spectral_score,
            pitch_consistency=pitch_score,
            noise_detection=noise_score,
            ml_score=ml_score,
            edit_detection=edit_score,
            artifacts=artifacts
        )
        
        return AnalysisResponse(
            is_ai_generated=is_ai_generated,
            is_manipulated=is_manipulated,
            confidence=overall_score,
            analysis_type="audio",
            audio_details=audio_details,
            metadata=metadata,
            processing_time=0.0  # Will be set by main.py
        )
    
    def _extract_metadata(self, file_path: Path, audio_data: np.ndarray, sr: int) -> MediaMetadata:
        """Extract metadata from audio file"""
        duration = librosa.get_duration(y=audio_data, sr=sr)
        file_size = file_path.stat().st_size
        
        # Try to get original file info
        try:
            info = sf.info(str(file_path))
            channels = info.channels
            original_sr = info.samplerate
        except:
            channels = 1
            original_sr = sr
        
        return MediaMetadata(
            duration=duration,
            format=file_path.suffix[1:],  # Remove dot
            size=file_size,
            sample_rate=original_sr,
            channels=channels
        )
    
    def _analyze_spectral_features(self, audio_data: np.ndarray, sr: int) -> float:
        """
        Analyze spectral features for AI generation indicators
        
        AI-generated audio often has:
        - Unnaturally smooth spectral transitions
        - Consistent spectral patterns
        - Limited high-frequency content
        """
        # Compute spectral centroid
        spectral_centroids = librosa.feature.spectral_centroid(y=audio_data, sr=sr)[0]
        
        # Compute spectral rolloff
        spectral_rolloff = librosa.feature.spectral_rolloff(y=audio_data, sr=sr)[0]
        
        # Compute spectral bandwidth
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=audio_data, sr=sr)[0]
        
        # Calculate variance (AI audio tends to have lower variance)
        centroid_var = np.var(spectral_centroids)
        rolloff_var = np.var(spectral_rolloff)
        bandwidth_var = np.var(spectral_bandwidth)
        
        # Normalize and combine scores
        # Lower variance = higher AI probability
        centroid_score = 1.0 - min(centroid_var / 10000000, 1.0)
        rolloff_score = 1.0 - min(rolloff_var / 10000000, 1.0)
        bandwidth_score = 1.0 - min(bandwidth_var / 1000000, 1.0)
        
        return (centroid_score + rolloff_score + bandwidth_score) / 3
    
    def _analyze_pitch_consistency(self, audio_data: np.ndarray, sr: int) -> float:
        """
        Analyze pitch consistency
        
        AI-generated speech often has:
        - Too consistent pitch
        - Unnatural pitch transitions
        - Limited pitch variation
        """
        # Extract pitch using piptrack
        pitches, magnitudes = librosa.piptrack(y=audio_data, sr=sr)
        
        # Get pitch values where magnitude is highest
        pitch_values = []
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            if pitch > 0:  # Only consider non-zero pitches
                pitch_values.append(pitch)
        
        if len(pitch_values) < 10:
            return 0.5  # Not enough data
        
        pitch_values = np.array(pitch_values)
        
        # Calculate pitch variation
        pitch_std = np.std(pitch_values)
        pitch_range = np.ptp(pitch_values)  # Peak to peak
        
        # AI audio tends to have lower variation
        # Normalize scores (typical human speech has std > 50, range > 100)
        std_score = 1.0 - min(pitch_std / 100, 1.0)
        range_score = 1.0 - min(pitch_range / 200, 1.0)
        
        return (std_score + range_score) / 2
    
    def _detect_artificial_noise(self, audio_data: np.ndarray, sr: int) -> float:
        """
        Detect artificial noise patterns
        
        AI-generated audio may have:
        - Synthetic background noise
        - Periodic noise patterns
        - Unnatural silence gaps
        """
        # Compute zero crossing rate
        zcr = librosa.feature.zero_crossing_rate(audio_data)[0]
        
        # Compute RMS energy
        rms = librosa.feature.rms(y=audio_data)[0]
        
        # Calculate consistency (AI tends to be more consistent)
        zcr_var = np.var(zcr)
        rms_var = np.var(rms)
        
        # Lower variance in noise = higher AI probability
        zcr_score = 1.0 - min(zcr_var / 0.01, 1.0)
        rms_score = 1.0 - min(rms_var / 0.01, 1.0)
        
        return (zcr_score + rms_score) / 2
    
    def _detect_artifacts(self, audio_data: np.ndarray, sr: int) -> List[ArtifactDetection]:
        """
        Detect specific artifacts in audio
        
        Returns list of detected artifacts with confidence scores
        """
        artifacts = []
        
        # Detect clipping
        clipping_ratio = np.sum(np.abs(audio_data) > 0.99) / len(audio_data)
        if clipping_ratio > 0.01:
            artifacts.append(ArtifactDetection(
                type="audio_clipping",
                confidence=min(clipping_ratio * 10, 1.0),
                description=f"Audio clipping detected in {clipping_ratio*100:.2f}% of samples"
            ))
        
        # Detect unnatural silence
        rms = librosa.feature.rms(y=audio_data)[0]
        silence_threshold = 0.01
        silence_ratio = np.sum(rms < silence_threshold) / len(rms)
        if silence_ratio > 0.3:
            artifacts.append(ArtifactDetection(
                type="unnatural_silence",
                confidence=min(silence_ratio, 1.0),
                description=f"Excessive silence detected ({silence_ratio*100:.1f}% of audio)"
            ))
        
        # Detect spectral discontinuities
        spectral_contrast = librosa.feature.spectral_contrast(y=audio_data, sr=sr)
        contrast_changes = np.abs(np.diff(spectral_contrast, axis=1))
        high_changes = np.sum(contrast_changes > 20) / contrast_changes.size
        if high_changes > 0.1:
            artifacts.append(ArtifactDetection(
                type="spectral_discontinuity",
                confidence=min(high_changes * 5, 1.0),
                description="Abrupt spectral changes detected (possible AI artifact)"
            ))
        
        # Detect manual edits/cuts
        edit_score = self._detect_manual_edits(audio_data, sr)
        if edit_score > 0.4:
            artifacts.append(ArtifactDetection(
                type="manual_edit_suspected",
                confidence=min(edit_score, 1.0),
                description="Audio transitions suggest possible manual editing"
            ))
        
        return artifacts
    
    def _detect_manual_edits(self, audio_data: np.ndarray, sr: int) -> float:
        """
        Detect possible manual edits or cuts in audio
        
        Returns score 0-1 where 1 = highly likely edited
        """
        # 1. Detect abrupt changes in spectral flux (cuts between segments)
        spectral_flux = librosa.onset.onset_strength(y=audio_data, sr=sr)
        
        # Find peaks in spectral flux
        from scipy.signal import find_peaks
        peaks, properties = find_peaks(spectral_flux, height=np.mean(spectral_flux) * 3.0, distance=sr//10)
        
        # 2. Detect noise floor changes (different recording environments)
        hop_length = 512
        frames = len(audio_data) // hop_length
        segment_size = sr  # 1 second
        num_segments = len(audio_data) // segment_size
        
        if num_segments < 3:
            return 0.0
        
        noise_levels = []
        for i in range(num_segments):
            start = i * segment_size
            end = start + segment_size
            segment = audio_data[start:end]
            noise_level = np.std(segment)
            noise_levels.append(noise_level)
        
        noise_variation = np.std(noise_levels) / (np.mean(noise_levels) + 1e-10)
        
        # 3. Combine scores
        peak_density = min(len(peaks) / (len(audio_data) / sr) * 2.0, 1.0)
        noise_score = min(noise_variation, 1.0)
        
        edit_score = (peak_density * 0.5 + noise_score * 0.5)
        return float(edit_score)
    
    def _ml_deepfake_score(self, file_path: Path) -> Optional[float]:
        """
        Placeholder for ML deepfake score
        
        Currently uses heuristics. Future improvement: load real audio
        deepfake detection model from Hugging Face.
        """
        return None
