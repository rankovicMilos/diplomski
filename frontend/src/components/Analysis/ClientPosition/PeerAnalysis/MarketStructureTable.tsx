type MarketStructureTable = {
  metrics: {
    total_assets: {
      metric_name_sr: string,
      metric_name_en: string,
      aop_code: string,
      companies: {
        name: string,
        value: number,
        market_share_pct: number,
        rank: number
      }[],
      industry_total: number
    },
    total_revenue: {
      metric_name_sr: string,
      metric_name_en: string,
      aop_code: string,
      companies: {
        name: string,
        value: number,
        market_share_pct: number,
        rank: number
      }[],
      industry_total: number
    },
    operating_revenue: {
      metric_name_sr: string,
      metric_name_en: string,
      aop_code: string,
      companies: {
        name: string,
        value: number,
        market_share_pct: number,
        rank: number
      }[],
      industry_total: number
    },
    revenue_from_goods: {
      metric_name_sr: string,
      metric_name_en: string,
      aop_code: string,
      companies: {
        name: string,
        value: number,
        market_share_pct: number,
        rank: number
      }[],
      industry_total: number
    },
    revenue_from_products_services: {
      metric_name_sr: string,
      metric_name_en: string,
      aop_code: string,
      companies: {
        name: string,
        value: number,
        market_share_pct: number,
        rank: number
      }[],
      industry_total: number
    },
    total_expenses: {
      metric_name_sr: string,
      metric_name_en: string,
      aop_code: string,
      companies: {
        name: string,
        value: number,
        market_share_pct: number,
        rank: number
      }[],
      industry_total: number
    }
  }
}

const MarketStructureTable = ({ metrics }: MarketStructureTable) => {

  const mappedMetrics = Object.entries(metrics).map(([key, value]) => ({
    key: value.metric_name_en,
    value: value.industry_total
  }))

  return (
    <table className='w-[60%] mb-2'>
      <thead className="bg-teal-40 font-bold text-sm">
        <tr>
          <th className="text-start">Pokazatelj</th>
          <th>Ukupno za industriju</th>
        </tr>
      </thead>
      <tbody className="text-xs even:[&>tr]:bg-teal-10">
        {mappedMetrics.map((m) => (
          <tr key={m.key}>
            <td className="text-start">
              {m.key}
            </td>
            <td>
              {m?.value?.toLocaleString() ?? "-"}
            </td>
          </tr>
        ))}

      </tbody>
    </table>
  )
}

export default MarketStructureTable;