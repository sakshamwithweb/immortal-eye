'use client';

import AddContact from '@/components/AddContact';
import { Button } from '@/components/ui/button';
import { Play } from 'lucide-react';
import { useRef, useState } from 'react';

export default function RecordPage() {
  const [videoStarted, setVideoStarted] = useState(false)
  const [caretakerNumbers, setCaretakerNumbers] = useState([])
  const videoRef = useRef(null);
  const videoDuration = 30_000; // It is numeric seperator same like int that makes large number easier to read

  const startRecording = async (loc) => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: 640,
          height: 360,
          frameRate: 15,
          facingMode: { exact: 'environment' }
        },
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
              form.append('numbers', JSON.stringify({
                "caretakers": caretakerNumbers, // Dummy phone numbers, task: Make a form like that takes caretakers number then send here
              }));
              form.append('location', JSON.stringify(loc.toJSON()))

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
      alert("Something went wrong")
    }
  };

  const requestLocation = () => {
    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(
        ({ coords }) => {
          setVideoStarted(true)
          startRecording(coords)
        },
        (error) => alert("Error fetching location:"),
        { enableHighAccuracy: true }
      );
    } else {
      alert("Geolocation is not supported in your browser");
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4 gap-4">
      {videoStarted ? (
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className="border rounded-md"
          width={640}
          height={360}
        ></video>
      ) : (
        <>
          <AddContact caretakerNumbers={caretakerNumbers} setCaretakerNumbers={setCaretakerNumbers} />

          <Button onClick={requestLocation}> {/* btn -> requestLocation -> startRecording(location) */}
            Start Recording <Play />
          </Button>
        </>
      )}
    </div>
  );
}
