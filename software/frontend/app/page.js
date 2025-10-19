'use client';

import { useRef, useState } from 'react';

export default function RecordPage() {
  const videoRef = useRef(null);
  const videoDuration = 30_000; // It is numeric seperator same like int that makes large nuber easier to read

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 360, frameRate: 15 },
        audio: true,
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }

      const mime = MediaRecorder.isTypeSupported('video/webm;codecs=vp8,opus')
        ? 'video/webm;codecs=vp8,opus'
        : 'video/webm';

      const recordChunk = () => {
        return new Promise((resolve) => {
          const recorder = new MediaRecorder(stream, {
            mimeType: mime,
            videoBitsPerSecond: 500_000,
          });

          recorder.ondataavailable = async (e) => {
            if (e.data.size > 0) {
              const blob = e.data;
              const file = new File([blob], `clip_${Date.now()}.webm`, {
                type: blob.type,
              });

              const form = new FormData();
              form.append('clip', file);

              try {
                await fetch(
                  `${process.env.NEXT_PUBLIC_SERVER_URL}/upload`,
                  {
                    method: 'POST',
                    body: form,
                  }
                );
              } catch (err) {
                console.error('Upload failed:', err);
              }
            }
          };

          recorder.onstop = () => resolve();

          recorder.start();
          setTimeout(() => recorder.stop(), videoDuration); // 30 seconds
        });
      };

      while (true) {
        await recordChunk();
      }
    } catch (err) {
      console.error('Error accessing camera/mic:', err);
      alert("Something went wrong")
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4">
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className="border rounded-md"
        width={640}
        height={360}
      ></video>
      <button
        onClick={startRecording}
        className="mt-4 px-4 py-2 text-white rounded border bg-gray-500"
      >
        Start Recording
      </button>
    </div>
  );
}
