"use client";

import { QueryClientProvider as QueryProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { ReactNode } from "react";
import { getQueryClient } from "./getQueryClient";

const QueryClientProvider = ({
	children
}: {
	children: ReactNode | ReactNode[];
}) => {
	const queryClient = getQueryClient();

	return (
		<QueryProvider client={queryClient}>
			{children}
			<ReactQueryDevtools initialIsOpen={false} />
		</QueryProvider>
	);
};

export default QueryClientProvider;
