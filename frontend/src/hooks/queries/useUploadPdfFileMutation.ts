import { uploadPdfFile } from "@/src/lib/api";
import { UploadedFile } from "@/src/components/DragAndDropFile/DragAndDropFile";
import { useMutation } from "@tanstack/react-query";

const useUploadPdfFileMutation = () =>
	useMutation({
		mutationFn: async (file: UploadedFile) => {
			const res = await uploadPdfFile(file);
			if (res.status === 200) return res;
			throw new Error("Neuspelo otpremanje PDF datoteke");
		},
		retry: false,
	});

export default useUploadPdfFileMutation;
