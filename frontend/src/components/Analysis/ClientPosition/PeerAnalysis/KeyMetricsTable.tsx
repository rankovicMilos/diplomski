import capitalizeWords from "@/src/utils/helpers/capitalizeWords"

type KeyMetricsTableProps = {
  companies: {
    name: string,
    value: number,
    market_share_pct: number,
    rank: number
  }[]
}

const KeyMetricsTable = ({ companies }: KeyMetricsTableProps) => {

  return (
    <table className='w-[95%] mb-2'>
      <thead className="bg-teal-40 font-bold text-sm">
        <tr>
          <th>Preduzeće</th>
          <th>Ukupna aktiva (RSD)</th>
          <th>Tržišni udeo</th>
          <th>Rang</th>
        </tr>
      </thead>
      <tbody className="text-xs even:[&>tr]:bg-teal-10">
        {companies.map((company) => (
          <tr key={company.name}>
            <td>
              {capitalizeWords(company.name)}
            </td>
            <td>
              {company?.value?.toLocaleString() ?? "-"}
            </td>
            <td>
              {company.market_share_pct}%
            </td>
            <td>
              {company.rank}
            </td>
          </tr>
        ))}

      </tbody>
    </table>
  )
}

export default KeyMetricsTable;