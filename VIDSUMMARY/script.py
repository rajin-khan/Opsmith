#!/usr/bin/env python3
"""
Video Transcript and Summary Generator

This script processes a folder of videos, extracts audio, generates transcripts using Groq's
Whisper API, and creates comprehensive summaries using Groq's LLM.

Usage:
    python vidsum.py --input_folder ./test --output_folder ./output
"""

import os
import argparse
import subprocess
import json
from pathlib import Path
from typing import Optional
import time

# Try to import required libraries, suggest installation if not found
try:
    import groq
    from tqdm import tqdm
    from dotenv import load_dotenv
except ImportError:
    print("Required packages not found! Please install them:")
    print("pip install groq tqdm python-dotenv")
    exit(1)

# Load environment variables from .env file if it exists
dotenv_path = Path('.env')
if dotenv_path.exists():
    load_dotenv(dotenv_path)

def setup_conda_env():
    """Guide user to set up a conda environment."""
    print("\n=== Conda Environment Setup Guide ===")
    print("To create a dedicated conda environment for this project:")
    print("1. Run: conda create -y -n vidsummary python=3.10")
    print("2. Activate it: conda activate vidsummary")
    print("3. Install packages: pip install groq tqdm python-dotenv")
    print("4. Set your Groq API key: export GROQ_API_KEY=your_api_key_here")
    print("============================================\n")

def check_ffmpeg() -> bool:
    """Check if FFmpeg is installed and available."""
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except FileNotFoundError:
        return False

def extract_audio(video_path: Path, audio_path: Path) -> Path:
    """Extract audio from video using FFmpeg with optimized size."""
    print(f"Extracting audio from {video_path} to {audio_path}")
    
    # Using opus format in ogg container for maximum compression while maintaining quality
    # Opus is designed specifically for voice at low bitrates
    opus_path = audio_path.with_suffix('.ogg')
    
    # Command to extract and compress audio efficiently
    cmd = [
        "ffmpeg", 
        "-i", str(video_path),
        "-vn",                # No video
        "-c:a", "libopus",    # Use opus codec (excellent for speech at low bitrates)
        "-b:a", "16k",        # 16kbps bitrate (enough for speech recognition)
        "-ac", "1",           # Mono audio
        "-ar", "16000",       # 16kHz sample rate (standard for speech recognition)
        "-application", "voip", # Optimize for voice
        "-compression_level", "10", # Maximum compression
        "-y",                 # Overwrite output file
        str(opus_path)
    ]
    
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Check if Groq accepts opus format directly; if not, we'll need to convert to WAV
    # but we can still benefit from the smaller storage footprint until transcription time
    return opus_path

def get_audio_for_transcription(audio_path: Path) -> Path:
    """
    Ensure the audio is in a format compatible with Groq's Whisper API.
    Returns the path to the compatible audio file.
    """
    # If the file is already in a format we know Whisper accepts (like WAV), return it
    if audio_path.suffix.lower() == '.wav':
        return audio_path
        
    # Otherwise, convert to WAV for transcription
    wav_path = audio_path.with_suffix('.wav')
    
    # Only convert if the WAV file doesn't already exist
    if not wav_path.exists():
        cmd = [
            "ffmpeg",
            "-i", str(audio_path),
            "-ar", "16000",    # 16kHz sample rate
            "-ac", "1",        # Mono audio
            "-c:a", "pcm_s16le", # 16-bit PCM
            "-y",              # Overwrite output file
            str(wav_path)
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    return wav_path

def transcribe_audio(client, audio_path: Path, transcript_path: Path, model: str) -> Optional[str]:
    """Transcribe audio using Groq's Whisper API."""
    print(f"Transcribing {audio_path}")
    
    try:
        # Ensure the audio is in a compatible format for Groq's API
        compatible_audio_path = get_audio_for_transcription(audio_path)
        
        # For Groq's API, we need to send the file in a specific way
        with open(compatible_audio_path, "rb") as audio_file:
            # Create a file-like object with a name attribute to help with MIME type detection
            from io import BytesIO
            file_data = BytesIO(audio_file.read())
            file_data.name = str(compatible_audio_path)  # This helps with MIME type detection
            
            response = client.audio.transcriptions.create(
                model=model,
                file=file_data
            )
            
        transcript_text = response.text
        
        # Write transcript to file
        with open(transcript_path, "w") as f:
            f.write(transcript_text)
        
        return transcript_text
    except Exception as e:
        print(f"Error transcribing {audio_path}: {e}")
        # Add more detailed error handling for common issues
        if "file must be one of the following types" in str(e):
            print("  - This error suggests the audio file format is not recognized.")
            print("  - Let's try converting to a different format...")
            
            # Try converting to WAV format with standard parameters
            wav_path = audio_path.with_suffix('.wav')
            try:
                convert_cmd = [
                    "ffmpeg",
                    "-i", str(audio_path),
                    "-ar", "16000",  # 16kHz sample rate
                    "-ac", "1",      # Mono audio
                    "-c:a", "pcm_s16le",  # 16-bit PCM
                    "-y",            # Overwrite output file
                    str(wav_path)
                ]
                subprocess.run(convert_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                print(f"  - Converted to WAV format: {wav_path}")
                
                # Try again with the new format
                with open(wav_path, "rb") as wav_file:
                    file_data = BytesIO(wav_file.read())
                    file_data.name = str(wav_path)
                    
                    response = client.audio.transcriptions.create(
                        model=model,
                        file=file_data
                    )
                    
                transcript_text = response.text
                
                # Write transcript to file
                with open(transcript_path, "w") as f:
                    f.write(transcript_text)
                
                return transcript_text
                
            except Exception as wav_error:
                print(f"  - Error after conversion attempt: {wav_error}")
        
        return None

def summarize_transcript(client, transcript_text: str, summary_path: Path, model: str) -> Optional[str]:
    """Generate a comprehensive summary from the transcript using Groq's LLM."""
    print(f"Generating summary using {model}")
    
    # Create prompt with instruction to create a detailed, comprehensive summary
    prompt = f"""Please create a comprehensive summary (as markdown) of the following transcript. 
Do not miss any important information, facts, or key points from the original content.
Include all relevant details, names, dates, and specific information mentioned.
If any programming commands or terms or instructions are mentioned, add that to a cheatsheet (as a markdown table) that you will include at the end of the summary as implied from the transcript, if applicable; if not, do not even mention the cheatsheet.
The commands in the cheat sheet must be up to date and correct.
Do not ask questions, explain what you're doing, or include any commentary (e.g, "Here is a comprehensive summary", or "The transcript is as follows". Simply start with the content). 
Output only the final message as a readable Markdown Document — nothing else.

TRANSCRIPT:
{transcript_text}

COMPREHENSIVE SUMMARY:
"""
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        
        summary_text = response.choices[0].message.content
        
        # Write summary to file
        with open(summary_path, "w") as f:
            f.write(summary_text)
        
        return summary_text
    except Exception as e:
        print(f"Error generating summary: {e}")
        return None

def get_audio_file_size(file_path: Path) -> str:
    """Get human-readable file size of an audio file."""
    size_bytes = os.path.getsize(file_path)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0 or unit == 'GB':
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0

def process_video(client, video_path: Path, audio_folder: Path, transcript_folder: Path, summary_folder: Path, 
                  transcript_model: str, summary_model: str, skip_transcription: bool, skip_summarization: bool):
    """Process a single video: extract audio, transcribe, and summarize."""
    video_name = video_path.stem
    
    # Define output paths
    audio_path = audio_folder / f"{video_name}.ogg"  # Using Opus in Ogg container for storage
    transcript_path = transcript_folder / f"{video_name}.txt"
    summary_path = summary_folder / f"{video_name}_summary.md"
    
    # Step 1: Extract audio if needed
    if not audio_path.exists():
        audio_path = extract_audio(video_path, audio_path)
        print(f"Audio extracted. File size: {get_audio_file_size(audio_path)}")
    
    # Step 2: Transcribe audio if needed
    transcript_text = None
    if skip_transcription and transcript_path.exists():
        print(f"Using existing transcript for {video_name}")
        with open(transcript_path, "r") as f:
            transcript_text = f.read()
    else:
        transcript_text = transcribe_audio(client, audio_path, transcript_path, transcript_model)
    
    if not transcript_text:
        print(f"Failed to get transcript for {video_name}, skipping summarization")
        return
    
    # Step 3: Generate summary if needed
    if skip_summarization and summary_path.exists():
        print(f"Using existing summary for {video_name}")
    else:
        summary_text = summarize_transcript(client, transcript_text, summary_path, summary_model)
        if not summary_text:
            print(f"Failed to generate summary for {video_name}")

def main():
    # Configure command line arguments
    parser = argparse.ArgumentParser(description='Process videos for transcription and summarization')
    parser.add_argument('--input_folder', required=True, help='Folder containing video files')
    parser.add_argument('--output_folder', required=True, help='Folder to store transcripts and summaries')
    parser.add_argument('--api_key', required=False, help='Groq API key')
    parser.add_argument('--transcript_model', default='whisper-large-v3', help='Groq model for transcription')
    parser.add_argument('--summary_model', default='llama3-70b-8192', help='Groq model for summarization')
    parser.add_argument('--skip_transcription', action='store_true', help='Skip transcription if already done')
    parser.add_argument('--skip_summarization', action='store_true', help='Skip summarization if already done')
    parser.add_argument('--setup_conda', action='store_true', help='Display conda environment setup instructions')
    args = parser.parse_args()
    
    # Show conda setup instructions if requested and exit
    if args.setup_conda:
        setup_conda_env()
        return
    
    # Check FFmpeg installation
    if not check_ffmpeg():
        print("FFmpeg is not installed or not found in PATH.")
        print("Please install FFmpeg using: brew install ffmpeg")
        return
    
    # Create output folders if they don't exist
    output_folder = Path(args.output_folder)
    transcript_folder = output_folder / "transcripts"
    summary_folder = output_folder / "summaries"
    audio_folder = output_folder / "audio"
    
    os.makedirs(transcript_folder, exist_ok=True)
    os.makedirs(summary_folder, exist_ok=True)
    os.makedirs(audio_folder, exist_ok=True)
    
    # Use environment variable if API key is not provided as argument
    GROQ_API_KEY = args.api_key or os.environ.get("GROQ_API_KEY")
    
    if not GROQ_API_KEY:
        print("Groq API key is required. Set it using --api_key or GROQ_API_KEY environment variable.")
        print("You can run: export GROQ_API_KEY=your_api_key_here")
        print("Or create a .env file in the project root with GROQ_API_KEY=your_api_key_here")
        return
        
    # Use environment variables for models if not specified in arguments
    if args.transcript_model == "whisper-large-v3" and os.environ.get("TRANSCRIPT_MODEL"):
        args.transcript_model = os.environ.get("TRANSCRIPT_MODEL")
        
    if args.summary_model == "llama3-70b-8192" and os.environ.get("SUMMARY_MODEL"):
        args.summary_model = os.environ.get("SUMMARY_MODEL")
    
    # Initialize Groq client
    client = groq.Client(api_key=GROQ_API_KEY)
    
    # Get list of video files
    input_folder = Path(args.input_folder)
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv']
    video_files = [f for f in input_folder.glob('**/*') if f.suffix.lower() in video_extensions]
    
    if not video_files:
        print(f"No video files found in {input_folder}")
        return
    
    print(f"Found {len(video_files)} video files to process")
    
    # Process each video
    for video_path in tqdm(video_files, desc="Processing videos"):
        process_video(
            client, 
            video_path, 
            audio_folder, 
            transcript_folder, 
            summary_folder, 
            args.transcript_model, 
            args.summary_model, 
            args.skip_transcription, 
            args.skip_summarization
        )
    
    print("Processing complete!")
    print(f"Transcripts saved to: {transcript_folder}")
    print(f"Summaries saved to: {summary_folder}")

if __name__ == "__main__":
    main()