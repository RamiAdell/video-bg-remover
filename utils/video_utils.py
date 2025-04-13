import cv2
from rembg import remove

def remove_background_from_video(input_video_path, output_video_path, progress_callback):
    cap = cv2.VideoCapture(input_video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
    processed_frames = 0
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            frame_rgba = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
            output = remove(frame_rgba)
            output_bgr = cv2.cvtColor(output, cv2.COLOR_BGRA2BGR)
            out.write(output_bgr)
            processed_frames += 1
            progress_callback((processed_frames / frame_count) * 100)
    except Exception as e:
        print(f"Error processing video: {e}")
    finally:
        cap.release()
        out.release()