import capitalizeWords from "@/src/utils/helpers/capitalizeWords"

type CompanyProfilesTableProps = {
  companies: {
    name: string,
    total_assets: number,
    total_revenue: number,
    operating_revenue: number,
    revenue_from_goods: number,
    revenue_from_products_services: number,
    total_expenses: number,
    operating_result: number,
    revenue_mix: {
      goods_pct: number,
      products_services_pct: number
    },
    operating_margin_pct: number,
    asset_turnover: number
  }[]
}

const CompanyProfilesTable = ({ companies }: CompanyProfilesTableProps) => {

  const mapToMilions = (val: number) => {
    return `${val / 1000000}M`
  }

  return (
    <div className="flex flex-col gap-2">

      <h4 className="font-semibold text-teal-100">Finansijsko poređenje preduzeća</h4>
      <table className='w-[95%] mb-2'>
        <thead className="bg-teal-40 font-bold text-sm">
          <tr>
            <th>Preduzeće</th>
            <th>Ukupna aktiva</th>
            <th>Ukupni prihodi</th>
            <th>Oper. marža</th>
            <th>Obrt aktive</th>
            <th>Udeo robe %</th>
          </tr>
        </thead>
        <tbody className="text-xs even:[&>tr]:bg-teal-10">
          {companies.map((company) => (
            <tr key={company.name}>
              <td>
                {capitalizeWords(company.name)}
              </td>
              <td>
                {mapToMilions(company.total_assets)}
              </td>
              <td>
                {mapToMilions(company.total_revenue)}
              </td>
              <td>
                {company.operating_margin_pct}%
              </td>
              <td>
                {company.asset_turnover}x
              </td>
              <td>
                {company.revenue_mix.goods_pct}%
              </td>
            </tr>
          ))}

        </tbody>
      </table>
    </div>
  )
}

export default CompanyProfilesTable;