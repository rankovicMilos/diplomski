import { getClientAnalysis } from "@/src/lib/api";
import { useQuery } from "@tanstack/react-query";

const useClientPositionQuery = (marketPositionId: string) =>
	useQuery({
		queryKey: ["clientPosition", marketPositionId],
		queryFn: async () => {
			try {

        if (!marketPositionId) throw new Error('Potrebna je tržišna pozicija')

				const res = await getClientAnalysis(marketPositionId);
				
				if (res.status === 200) return res

				throw new Error("Neuspelo preuzimanje pozicije klijenta")

				} catch (error) {

					throw new Error(error instanceof Error ? error.message : 'Došlo je do nepoznate greške')
				}

		},
		retry: false,
	});

export default useClientPositionQuery;
