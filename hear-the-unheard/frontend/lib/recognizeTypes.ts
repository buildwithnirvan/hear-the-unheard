// Mirrors backend/app/websocket/recognize_ws.py's protocol exactly.
// Keep these in sync by hand — there's no shared schema generation yet.

export type StatusMessage = {
  type: "status";
  hands_present: boolean | null;
  pose_present: boolean;
  frame_index: number;
};

export type RecognitionMessage = {
  type: "recognition";
  gloss: string;
  confidence: number;
  window_frames: number;
  flushed_at_stream_end?: boolean;
};

export type ErrorMessage = {
  type: "error";
  detail: string;
};

export type StreamEndedMessage = {
  type: "stream_ended";
};

export type RecognizeWsMessage =
  | StatusMessage
  | RecognitionMessage
  | ErrorMessage
  | StreamEndedMessage;

export type RecognizedToken = {
  gloss: string;
  confidence: number;
  at: number; // Date.now() when received, for display/debugging only
};
