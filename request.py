"""
Simple test script to verify the /analyze endpoint.

Usage:
    python request.py <video_file.mp4> "<question text>"

Example:
    python request.py interview.mp4 "Explica una experiència de lideratge"
"""

import sys
import json
import requests


API_URL = "http://localhost:5000/analyze"


def main():
    if len(sys.argv) < 3:
        print("Usage: python request.py <video_file> <question>")
        print('Example: python request.py interview.mp4 "Explica una experiència"')
        sys.exit(1)

    video_path = sys.argv[1]
    question = sys.argv[2]

    print(f"Sending '{video_path}' to {API_URL}...")
    print(f"Question: {question}\n")

    with open(video_path, "rb") as f:
        response = requests.post(
            API_URL,
            files={"video": (video_path, f, "video/mp4")},
            data={"question": question},
        )

    print(f"Status: {response.status_code}\n")

    if response.status_code == 200:
        result = response.json()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Error: {response.text}")


if __name__ == "__main__":
    main()
