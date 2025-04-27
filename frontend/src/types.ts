export type FileMetadata = {
  id: string;
  name: string;
  content_type: string;
  size: number;
  is_indexed: boolean | null;
};
