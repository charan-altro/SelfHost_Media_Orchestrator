package services

import (
	"encoding/json"
	"os"
	"os/exec"
	"strings"
)

type MediaInfo struct {
	Resolution    string `json:"resolution"`
	HdrType       string `json:"hdr_type"`
	VideoCodec    string `json:"video_codec"`
	AudioCodec    string `json:"audio_codec"`
	AudioChannels string `json:"audio_channels"`
	SizeBytes     int64  `json:"size_bytes"`
}

// ExtractMediaInfo attempts to get technical specs using ffprobe (preferred)
func ExtractMediaInfo(filePath string) MediaInfo {
	info := MediaInfo{}

	fi, err := os.Stat(filePath)
	if err == nil {
		info.SizeBytes = fi.Size()
	}

	// Try ffprobe
	data, err := runFFProbe(filePath)
	if err == nil {
		parseFFProbeOutput(data, &info)
		return info
	}

	return info
}

type ffprobeOutput struct {
	Streams []struct {
		CodecType    string `json:"codec_type"`
		CodecName    string `json:"codec_name"`
		Width        int    `json:"width"`
		Height       int    `json:"height"`
		Channels     int    `json:"channels"`
		ColorSpace   string `json:"color_space"`
		ColorPrim    string `json:"color_primaries"`
		ColorTransfer string `json:"color_transfer"`
	} `json:"streams"`
}

func runFFProbe(filePath string) (*ffprobeOutput, error) {
	cmd := exec.Command("ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", filePath)
	out, err := cmd.Output()
	if err != nil {
		return nil, err
	}

	var data ffprobeOutput
	if err := json.Unmarshal(out, &data); err != nil {
		return nil, err
	}
	return &data, nil
}

func parseFFProbeOutput(data *ffprobeOutput, info *MediaInfo) {
	for _, s := range data.Streams {
		if s.CodecType == "video" && info.VideoCodec == "" {
			info.VideoCodec = s.CodecName
			
			// Resolution
			if s.Width >= 3800 {
				info.Resolution = "4K"
			} else if s.Width >= 1900 {
				info.Resolution = "1080p"
			} else if s.Width >= 1200 {
				info.Resolution = "720p"
			} else if s.Width > 0 {
				info.Resolution = "SD"
			}

			// Simple HDR detection
			if strings.Contains(s.ColorTransfer, "smpte2084") || strings.Contains(s.ColorPrim, "bt2020") {
				info.HdrType = "HDR"
			}
		} else if s.CodecType == "audio" && info.AudioCodec == "" {
			info.AudioCodec = s.CodecName
			switch s.Channels {
			case 8:
				info.AudioChannels = "7.1"
			case 6:
				info.AudioChannels = "5.1"
			case 2:
				info.AudioChannels = "2.0"
			default:
				if s.Channels > 0 {
					info.AudioChannels = string(rune(s.Channels))
				}
			}
		}
	}
}
