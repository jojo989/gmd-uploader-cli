import argparse
import asyncio
import os
from utils import upload_level, get_gmd_value_by_key

from typing import Any

def fill_arg_from_gmd(args, arg_name, gmd_key, gmd_content, cast_type: type[Any]=str, default=None):
    if getattr(args, arg_name, None) in (None, '', 0):
        value = get_gmd_value_by_key(gmd_content, gmd_key)
        try:
            setattr(args, arg_name, cast_type(value) if value is not None else default)
        except Exception:
            setattr(args, arg_name, default)

def main():
    parser = argparse.ArgumentParser(description="Upload a level to Geometry Dash server")
    parser.add_argument('-n', '--levelname', help="Level name")
    parser.add_argument('-d', '--description', default="", help="Level description")
    parser.add_argument('--id', "-id", type=int, default=0, help="Update existing level ID (default: 0 for new level)")
    parser.add_argument('--gameversion' , "-v", type=int, default=22, choices=range(0, 22), metavar="[0-22]", help="Game version number (21 or 22)")
    parser.add_argument('--levelversion', type=int, default=1, choices=range(1, 127), metavar="[1-127]", 
                        help="Level version number (max 127)")
    parser.add_argument('--gmd', "-gmd", required=True, help="Path to .gmd file containing level data")
    parser.add_argument('--songid', type=int, help="Song ID (overrides .gmd value if provided)")
    parser.add_argument('-usr', '--username', dest='username', required=True, help="Username")
    parser.add_argument('-pwd', '--password', dest='password', required=True, help="Password")
    parser.add_argument('-m', '--mode', type=int, default=0, choices=[0, 1, 2], 
                        help="Visibility mode: 0 (public), 1 (unlisted), 2 (friends only)")
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

    gmd_arg_map = [
        ('songid', 'k45', int, 0),
        ('levelname', 'k2', str, "wtf xd"),
        ('description', 'k3', str, ""),
        ('id', 'k1', int, 0),
        ('levelversion', 'k16', int, '1')
        
    ]
    for arg_name, gmd_key, cast_type, default in gmd_arg_map:
        fill_arg_from_gmd(args, arg_name, gmd_key, gmd_content, cast_type, default)

    level_string = get_gmd_value_by_key(gmd_content, 'k4')
    level_objects = get_gmd_value_by_key(gmd_content, 'k48')
    if level_objects is not None and level_objects.isdigit():
        objects = int(level_objects)
    else:
        objects = 1  # Default value or handle as needed
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
            level_version=args.levelversion,
            objects=objects
        ))
        print(f"Level ID: {result}")
    except Exception as e:
        print(f"Error uploading level: {e}")

if __name__ == "__main__":
    main()