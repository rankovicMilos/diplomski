import { getMarketPositions, GetMarketPositionsQueryParams } from "@/src/lib/api";
import { useQuery } from "@tanstack/react-query";

const useMarketPositionsQuery = ({clientName, category}: GetMarketPositionsQueryParams) =>
	useQuery({
		queryKey: ["marketPositions", clientName, category],
		queryFn: async () => {
			try {

				const res = await getMarketPositions({clientName, category});
				
				if (res.status === 200) return res

				throw new Error("Neuspelo preuzimanje tržišne pozicije")

				} catch (error) {

					throw new Error(error instanceof Error ? error.message : 'Došlo je do nepoznate greške')
				}

		},
		retry: false,
	});

export default useMarketPositionsQuery;
