import { getAnalysisForCategory } from "@/src/lib/api";
import { useQuery } from "@tanstack/react-query";

const useAnalysisQuery = (category: string, { enabled = true }: { enabled?: boolean } = {}) =>
	useQuery({
		enabled,
		queryKey: [
			"category",
			category,
		],
		queryFn: async () => {
			try {

				const res = await getAnalysisForCategory(category);
				
				if (res.status === 200) return res

				throw new Error("Neuspelo preuzimanje analize")

				} catch (error) {

					throw new Error(error instanceof Error ? error.message : 'Došlo je do nepoznate greške')
				}

		},
		retry: false,
	});

export default useAnalysisQuery;
