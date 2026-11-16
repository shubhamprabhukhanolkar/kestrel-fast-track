import { useEffect, useRef, useState } from "react";

export function useAppAudio() {
  const [enabled, setEnabled] = useState(
    () => localStorage.getItem("kestrel-audio") === "on",
  );
  const context = useRef(null);
  const enabledRef = useRef(enabled);
  enabledRef.current = enabled;
  function play(kind = "click") {
    if (!enabledRef.current) return;
    try {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      if (!AudioContext) return;
      context.current ||= new AudioContext();
      const audio = context.current;
      audio.resume().catch(() => {});
      const notes =
        kind === "success"
          ? [523, 659, 784]
          : kind === "error"
            ? [330, 247]
            : [660];
      notes.forEach((frequency, index) => {
        const oscillator = audio.createOscillator();
        const gain = audio.createGain();
        const start = audio.currentTime + index * 0.075;
        oscillator.type = "sine";
        oscillator.frequency.value = frequency;
        gain.gain.setValueAtTime(0, start);
        gain.gain.linearRampToValueAtTime(0.035, start + 0.01);
        gain.gain.exponentialRampToValueAtTime(0.0001, start + 0.12);
        oscillator.connect(gain);
        gain.connect(audio.destination);
        oscillator.start(start);
        oscillator.stop(start + 0.13);
        oscillator.onended = () => {
          oscillator.disconnect();
          gain.disconnect();
        };
      });
    } catch {
      /* Audio remains optional when a browser blocks playback. */
    }
  }
  useEffect(() => {
    const click = (event) => {
      const button = event.target.closest?.(
        'button, a, [role="tab"], [role="switch"]',
      );
      if (button && !button.disabled && !button.closest("[data-audio-toggle]"))
        play("click");
    };
    const feedback = () => play("error");
    document.addEventListener("click", click);
    window.addEventListener("kestrel-api-error", feedback);
    return () => {
      document.removeEventListener("click", click);
      window.removeEventListener("kestrel-api-error", feedback);
      context.current?.close().catch(() => {});
    };
  }, []);
  function toggle() {
    const next = !enabledRef.current;
    enabledRef.current = next;
    setEnabled(next);
    localStorage.setItem("kestrel-audio", next ? "on" : "off");
    if (next) play("success");
    else context.current?.suspend().catch(() => {});
  }
  return { enabled, toggle, play };
}
