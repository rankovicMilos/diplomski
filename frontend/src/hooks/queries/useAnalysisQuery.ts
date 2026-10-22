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

				throw new Error("Failed to fetch analysis")

				} catch (error) {

					throw new Error(error instanceof Error ? error.message : 'An unknown error occurred')
				}

		},
		retry: false,
	});

export default useAnalysisQuery;
