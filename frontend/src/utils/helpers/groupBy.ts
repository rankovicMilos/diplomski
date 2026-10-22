export const groupBy = <T, K extends string | number | symbol>(
	array: T[],
	getKey: (item: T, index: number, array: T[]) => K
): Record<K, T[]> =>
	array.reduce(
		(acc, item, index) => {
			const key = getKey(item, index, array);
			if (!acc[key]) {
				acc[key] = [];
			}
			acc[key].push(item);
			return acc;
		},
		{} as Record<K, T[]>
	);