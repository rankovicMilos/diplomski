import { generateMarketPosition, MarketPositionRequestBody } from "@/src/lib/api";
import { useMutation } from "@tanstack/react-query";

const useGenerateMarketPositionMutation = () =>
	useMutation({
		mutationFn: async (body: MarketPositionRequestBody) => {
			const res = await generateMarketPosition(body);
			if (res.status === 200 || res.status === 504) return res;
			throw new Error(`Failed to generate market position: ${res.data?.error}`);
		},
		retry: false,
	});

export default useGenerateMarketPositionMutation;
