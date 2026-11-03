'use client'
import cn from "@/src/utils/cn";
import { FileUploadOutlined } from "@mui/icons-material";
import { ChangeEvent, DragEvent, useCallback, useId, useState } from "react";

export interface UploadedFile {
  file: File;
  id: string;
  name: string;
  size: number;
  type: string;
  base64?: string;
}

type DragAndDropFileProps = {
  onSelectFile: (file: UploadedFile) => void,
}

const DragAndDropFile = ({ onSelectFile }: DragAndDropFileProps) => {
  const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
  const ALLOWED_TYPES = [
    'application/pdf',
    'text/csv',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  ];

  const [isDragging, setIsDragging] = useState(false);
  // One id per instance: a form can show several drop zones at once
  const inputId = useId();

  const handleDrag = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDragIn = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      setIsDragging(true);
    }
  }, []);

  const handleDragOut = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const droppedFile = e.dataTransfer.files[0];
    if (!droppedFile) return;

    if (e.dataTransfer.files.length > 1) {
      alert(`Možete otpremiti samo jednu datoteku odjednom!`);
      return;
    }

    if (droppedFile.size > MAX_FILE_SIZE) {
      alert(`Datoteka ${droppedFile.name} premašuje ograničenje od 10 MB`);
      return;
    }
    if (!ALLOWED_TYPES.includes(droppedFile.type)) {
      alert(`Tip datoteke ${droppedFile.type} nije dozvoljen`);
      return;
    }

    const uploadedFile: UploadedFile = {
      file: droppedFile,
      id: crypto.randomUUID(),
      name: droppedFile.name,
      size: droppedFile.size,
      type: droppedFile.type,
    };

    onSelectFile(uploadedFile);
  }, [onSelectFile]);

  const handleFileSelect = (e: ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    if (selectedFile.size > MAX_FILE_SIZE) {
      alert(`Datoteka ${selectedFile.name} premašuje ograničenje od 10 MB`);
      return;
    }
    if (!ALLOWED_TYPES.includes(selectedFile.type)) {
      alert(`Tip datoteke ${selectedFile.type} nije dozvoljen`);
      return;
    }

    const uploadedFile: UploadedFile = {
      file: selectedFile,
      id: crypto.randomUUID(),
      name: selectedFile.name,
      size: selectedFile.size,
      type: selectedFile.type,
    };

    onSelectFile(uploadedFile);
  };


  return (
    <div className="flex flex-col gap-3">
      <div
        role="button"
        tabIndex={0}
        aria-label="Otpremanje datoteke: prevucite i otpustite ili kliknite za izbor"
        className={cn("rounded-xs flex flex-col justify-center items-center py-16 border-1 border-dashed bg-yellow-10 hover:bg-yellow-20 border-yellow-100 cursor-pointer", {
          "bg-yellow-20": isDragging
        })}
        onDragEnter={handleDragIn}
        onDragLeave={handleDragOut}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => document.getElementById(inputId)?.click()}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            document.getElementById(inputId)?.click();
          }
        }}
      >
        <FileUploadOutlined sx={{ fontSize: 60 }} color="disabled" />

        <span className="text-md text-charcoal-90 font-semibold mt-4">
          Otpustite datoteku ovde
        </span>
        <span className="text-xs text-charcoal-70">
          ili kliknite da izaberete datoteku
        </span>
        <input
          id={inputId}
          type="file"
          accept="application/pdf,text/csv,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
          onChange={handleFileSelect}
          className="hidden"
        />
      </div>
    </div>
  )
}

export default DragAndDropFile