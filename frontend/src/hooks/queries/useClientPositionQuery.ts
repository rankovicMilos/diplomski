import { getClientAnalysis } from "@/src/lib/api";
import { useQuery } from "@tanstack/react-query";

const useClientPositionQuery = (marketPositionId: string) =>
	useQuery({
		queryKey: ["clientPosition", marketPositionId],
		queryFn: async () => {
			try {

        if (!marketPositionId) throw new Error('Market position is required')

				const res = await getClientAnalysis(marketPositionId);
				
				if (res.status === 200) return res

				throw new Error("Failed to fetch client position")

				} catch (error) {

					throw new Error(error instanceof Error ? error.message : 'An unknown error occurred')
				}

		},
		retry: false,
	});

export default useClientPositionQuery;
