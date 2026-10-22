import { uploadSheetFile } from "@/src/lib/api";
import { useMutation } from "@tanstack/react-query";

export interface UploadSheetFileParams {
	fileName: string;
	base64: string;
}

const useUploadSheetFileMutation = () =>
	useMutation({
		mutationFn: async ({ fileName, base64 }: UploadSheetFileParams) => {
			const res = await uploadSheetFile(fileName, base64);
			if (res.status === 200) return res;
			throw new Error("Failed to upload sheet file");
		},
		retry: false,
	});

export default useUploadSheetFileMutation;
