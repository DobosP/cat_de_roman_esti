export interface PrecompressedBinding {
  file: string;
  bytes: number;
  sha256: string;
  gzip: { file: string; bytes: number; sha256: string };
  br: { file: string; bytes: number; sha256: string };
}
export function emitPrecompressedAssets(directory: string): readonly PrecompressedBinding[];
