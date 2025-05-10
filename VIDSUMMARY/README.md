# VIDSUMMARY

A Python tool that processes video files to generate transcripts and comprehensive summaries using Groq's AI services.

## Overview

This tool automates the workflow of:
1. Extracting audio from video files (using FFmpeg)
2. Transcribing the audio to text (using Groq's Whisper API)
3. Generating comprehensive summaries (using Groq's LLM)

## Project Structure

```
VIDSUMMARY/
├── script.py         # Main script
├── .env              # Environment variables (for API key)
├── input/            # Input folder for videos
└── output/           # Output folder structure
    ├── audio/        # Extracted audio files (Opus format)
    ├── transcripts/  # Raw text transcripts
    └── summaries/    # Comprehensive summaries
```

## Requirements

* Python 3.8+
* FFmpeg (with libopus support)
* Groq API key
* Required Python packages:
   * `groq`
   * `tqdm`
   * `python-dotenv`

## Setup

1. Install required Python packages:

```bash
pip install groq tqdm python-dotenv
```

2. Set your Groq API key:

```bash
# Either export it directly
export GROQ_API_KEY=your_api_key_here

# Or create a .env file in the project root
echo "GROQ_API_KEY=your_api_key_here" > .env
```

3. (Optional) Create a dedicated conda environment:

```bash
# Get setup instructions
python script.py --setup_conda

# Then follow the displayed steps
```

4. Ensure FFmpeg is installed with libopus support:
   * On macOS: `brew install ffmpeg`
   * On Ubuntu: `sudo apt install ffmpeg`
   * On Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html)

## Usage

Process a folder of videos:

```bash
python script.py --input_folder ./input --output_folder ./output
```

## Command-line Options

* `--input_folder`: Folder containing video files (required)
* `--output_folder`: Folder to store output files (required)
* `--api_key`: Directly provide a Groq API key (alternatively use the GROQ_API_KEY environment variable)
* `--transcript_model`: Specify the Groq model for transcription (default: whisper-large-v3)
* `--summary_model`: Specify the Groq model for summarization (default: llama3-70b-8192)
* `--skip_transcription`: Skip transcription if transcript files already exist
* `--skip_summarization`: Skip summarization if summary files already exist
* `--setup_conda`: Display conda environment setup instructions

## Examples

Basic usage:

```bash
python script.py --input_folder ./input --output_folder ./output
```

Using a different model for summarization (view available from [groq's playground](https://console.groq.com/playground)):

```bash
python script.py --input_folder ./input --output_folder ./output --summary_model llama3-70b-8192
```

Skip re-transcribing existing files:

```bash
python script.py --input_folder ./input --output_folder ./output --skip_transcription
```

## Audio Processing

The script uses a two-stage audio handling approach for maximum efficiency:

1. **Storage Optimization**: 
   * Extracts audio using Opus codec in Ogg container
   * Uses highly efficient settings optimized for speech:
     * 16kbps bitrate
     * 16kHz sample rate
     * Mono audio
     * VoIP optimization 
     * Maximum compression level
   * Typically reduces file size by 80-95% compared to WAV

2. **Transcription Compatibility**:
   * Automatically converts to compatible WAV format for Groq's API when needed
   * WAV conversion settings:
     * 16kHz sample rate
     * Mono audio
     * 16-bit PCM encoding

This approach provides minimum disk usage while ensuring compatibility with Groq's Whisper API.

## Environment Variables

You can also configure the tool using environment variables:
* `GROQ_API_KEY`: Your Groq API key
* `TRANSCRIPT_MODEL`: Override the default transcription model
* `SUMMARY_MODEL`: Override the default summarization model

## Important Notes

* The script uses the highly efficient Opus audio codec for storage, which dramatically reduces file sizes while maintaining excellent speech quality
* Audio is automatically converted to the appropriate format for Groq's API at transcription time
* The script includes error handling for audio conversion issues and will attempt to convert problematic audio files
* For large videos, be aware of potential API rate limits and costs associated with Groq's services
* The script supports various video formats including: .mp4, .avi, .mov, .mkv, .webm, .flv, .wmv