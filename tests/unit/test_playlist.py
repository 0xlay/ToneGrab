"""Tests for playlist download functionality."""

import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from src.core.downloader import (
    AudioDownloader,
    AudioFormat,
    DownloadResult,
)


class TestPlaylistDownload(unittest.TestCase):
    """Test playlist download functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_output_dir = Path("test_output")
        self.downloader = AudioDownloader(self.test_output_dir)

    @patch("src.core.downloader.VideoInfoExtractor")
    def test_is_playlist_returns_true_for_playlist_url(self, mock_extractor):
        """Test that is_playlist correctly identifies playlist URLs."""
        # Mock playlist info
        mock_info = {
            "_type": "playlist",
            "title": "Test Playlist",
            "entries": [{"id": "1"}, {"id": "2"}],
        }
        
        mock_extractor_instance = Mock()
        mock_extractor_instance.extract_info.return_value = mock_info
        self.downloader._info_extractor = mock_extractor_instance

        result = self.downloader.is_playlist("https://youtube.com/playlist?list=123")
        
        self.assertTrue(result)

    @patch("src.core.downloader.VideoInfoExtractor")
    def test_is_playlist_returns_false_for_single_video(self, mock_extractor):
        """Test that is_playlist returns False for single video URLs."""
        # Mock single video info
        mock_info = {
            "_type": "video",
            "title": "Test Video",
            "id": "abc123",
        }
        
        mock_extractor_instance = Mock()
        mock_extractor_instance.extract_info.return_value = mock_info
        self.downloader._info_extractor = mock_extractor_instance

        result = self.downloader.is_playlist("https://youtube.com/watch?v=abc123")
        
        self.assertFalse(result)

    @patch("src.core.downloader.VideoInfoExtractor")
    @patch("src.core.downloader.YtDlpDownloadStrategy")
    def test_download_playlist_downloads_all_items(self, mock_strategy, mock_extractor):
        """Test that download_playlist downloads all items in playlist."""
        # Mock playlist info
        mock_info = {
            "_type": "playlist",
            "title": "Test Playlist",
            "entries": [
                {"id": "1", "url": "https://example.com/1", "title": "Track 1"},
                {"id": "2", "url": "https://example.com/2", "title": "Track 2"},
                {"id": "3", "url": "https://example.com/3", "title": "Track 3"},
            ],
        }
        
        mock_extractor_instance = Mock()
        mock_extractor_instance.extract_info.return_value = mock_info
        self.downloader._info_extractor = mock_extractor_instance
        
        # Mock successful downloads
        mock_strategy_instance = Mock()
        mock_strategy_instance.download.return_value = "test_file.mp3"
        self.downloader._download_strategy = mock_strategy_instance

        results = self.downloader.download_playlist(
            url="https://youtube.com/playlist?list=123",
            audio_format="mp3",
            quality="192",
        )

        # Verify all items were downloaded
        self.assertEqual(len(results), 3)
        self.assertTrue(all(r.success for r in results))
        self.assertEqual(mock_strategy_instance.download.call_count, 3)

    @patch("src.core.downloader.VideoInfoExtractor")
    def test_download_playlist_handles_empty_playlist(self, mock_extractor):
        """Test that download_playlist handles empty playlists gracefully."""
        # Mock empty playlist
        mock_info = {
            "_type": "playlist",
            "title": "Empty Playlist",
            "entries": [],
        }
        
        mock_extractor_instance = Mock()
        mock_extractor_instance.extract_info.return_value = mock_info
        self.downloader._info_extractor = mock_extractor_instance

        results = self.downloader.download_playlist(
            url="https://youtube.com/playlist?list=123"
        )

        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].success)
        self.assertIn("empty", results[0].error_message.lower())

    @patch("src.core.downloader.VideoInfoExtractor")
    @patch("src.core.downloader.YtDlpDownloadStrategy")
    def test_download_playlist_calls_item_callback(self, mock_strategy, mock_extractor):
        """Test that download_playlist calls item callback for each item."""
        # Mock playlist info
        mock_info = {
            "_type": "playlist",
            "title": "Test Playlist",
            "entries": [
                {"id": "1", "url": "https://example.com/1", "title": "Track 1"},
                {"id": "2", "url": "https://example.com/2", "title": "Track 2"},
            ],
        }
        
        mock_extractor_instance = Mock()
        mock_extractor_instance.extract_info.return_value = mock_info
        self.downloader._info_extractor = mock_extractor_instance
        
        mock_strategy_instance = Mock()
        mock_strategy_instance.download.return_value = "test_file.mp3"
        self.downloader._download_strategy = mock_strategy_instance

        # Mock item callback
        item_callback = Mock()

        self.downloader.download_playlist(
            url="https://youtube.com/playlist?list=123",
            item_callback=item_callback,
        )

        # Verify callback was called for each item
        self.assertEqual(item_callback.call_count, 2)
        item_callback.assert_any_call(1, 2, "Track 1")
        item_callback.assert_any_call(2, 2, "Track 2")

    @patch("src.core.downloader.VideoInfoExtractor")
    @patch("src.core.downloader.YtDlpDownloadStrategy")
    def test_download_playlist_handles_failed_items(self, mock_strategy, mock_extractor):
        """Test that download_playlist continues even if some items fail."""
        # Mock playlist info
        mock_info = {
            "_type": "playlist",
            "title": "Test Playlist",
            "entries": [
                {"id": "1", "url": "https://example.com/1", "title": "Track 1"},
                {"id": "2", "url": "https://example.com/2", "title": "Track 2"},
                {"id": "3", "url": "https://example.com/3", "title": "Track 3"},
            ],
        }
        
        mock_extractor_instance = Mock()
        mock_extractor_instance.extract_info.return_value = mock_info
        self.downloader._info_extractor = mock_extractor_instance
        
        # Mock strategy to fail on second item
        mock_strategy_instance = Mock()
        mock_strategy_instance.download.side_effect = [
            "track1.mp3",  # Success
            Exception("Download failed"),  # Failure
            "track3.mp3",  # Success
        ]
        self.downloader._download_strategy = mock_strategy_instance

        results = self.downloader.download_playlist(
            url="https://youtube.com/playlist?list=123"
        )

        # All items should have results (even failed ones)
        self.assertEqual(len(results), 3)
        
        # Check individual results
        self.assertTrue(results[0].success)
        self.assertFalse(results[1].success)
        self.assertTrue(results[2].success)


if __name__ == "__main__":
    unittest.main()
