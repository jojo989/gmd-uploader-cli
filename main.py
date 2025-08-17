import argparse
import asyncio
import os
from utils import upload_level, get_gmd_value_by_key

def main():
    parser = argparse.ArgumentParser(description="Upload a level to Geometry Dash server")
    parser.add_argument('-n', '--levelname', required=True, help="Level name")
    parser.add_argument('-d', '--description', default="", help="Level description")
    parser.add_argument('--id', "-id", type=int, default=0, help="Update existing level ID (default: 0 for new level)")
    parser.add_argument('--gameversion' , "-v", type=int, default=22, choices=range(0, 22), metavar="[0-22]", help="Game version number (21 or 22)")
    parser.add_argument('--levelversion', type=int, default=127, choices=range(1, 127), metavar="[1-127]", 
                        help="Level version number (max 127)")
    parser.add_argument('--gmd', "-gmd", required=True, help="Path to .gmd file containing level data")
    parser.add_argument('-usr', '--username', dest='username', required=True, help="Username")
    parser.add_argument('-pwd', '--password', dest='password', required=True, help="Password")
    parser.add_argument('-m', '--mode', type=int, default=0, choices=[0, 1, 2], 
                        help="Visibility mode: 0 (public), 1 (unlisted), 2 (friends only)")
    parser.add_argument('--songid', help="Newgrounds song ID", default=get_gmd_value_by_key(gmd_content, 'k35'))

    args = parser.parse_args()
    if not args.gmd.lower().endswith('.gmd'):
        print(f"Error: '{args.gmd}' is not a .gmd file. Please provide a valid .gmd file.")
        return
    try:
        with open(args.gmd, 'r', encoding='utf-8') as f:
            gmd_content = f.read()
    except FileNotFoundError:
        print(f"Error: .gmd file '{args.gmd}' not found")
        return
    except Exception as e:
        print(f"Error reading .gmd file: {e}")
        return

    level_string = get_gmd_value_by_key(gmd_content, 'k4')
    if not level_string:
        print("Error: Could not extract level string from .gmd file (key 'k4' not found)")
        return

    try:
        result = asyncio.run(upload_level(
            username=args.username,
            password=args.password,
            levelname=args.levelname,
            leveldesc=args.description,
            lvlstr=level_string,
            audio_track=0,
            song_id=args.songid, 
            ver=args.gameversion,
            unlisted=args.mode,
            level_version=args.levelversion
        ))
        print(f"Level ID: {result}")
    except Exception as e:
        print(f"Error uploading level: {e}")

if __name__ == "__main__":
    main()