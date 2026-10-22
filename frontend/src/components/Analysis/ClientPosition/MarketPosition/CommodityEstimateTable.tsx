type CommodityEstimateTableProps = {
  estimated_volume: {
    low_estimate_tonnes: number,
    mid_estimate_tonnes: number,
    high_estimate_tonnes: number
  },
  market_share: {
    low_estimate_pct: number,
    mid_estimate_pct: number,
    high_estimate_pct: number
  }
}

const CommodityEstimateTable = ({ estimated_volume, market_share }: CommodityEstimateTableProps) => {

  return (
    <table className='w-[80%] mt-4'>
      <caption className="text-start text-2xs">Volume & Market Share Estimation</caption>
      <thead className="bg-teal-40 font-bold text-sm">
        <tr>
          <th>Scenario</th>
          <th>Estimated Volume</th>
          <th>Market Share</th>
        </tr>
      </thead>
      <tbody className="text-xs even:[&>tr]:bg-teal-10">
        <tr>
          <td>
            Low Estimate
          </td>
          <td>
            {estimated_volume?.low_estimate_tonnes?.toLocaleString()}
          </td>
          <td>
            {`${market_share?.low_estimate_pct}%`}
          </td>
        </tr>
        <tr>
          <td>
            Mid Estimate
          </td>
          <td>
            {estimated_volume?.mid_estimate_tonnes?.toLocaleString()}
          </td>
          <td>
            {`${market_share?.mid_estimate_pct}%`}
          </td>
        </tr>
        <tr>
          <td>
            High Estimate
          </td>
          <td>
            {estimated_volume?.high_estimate_tonnes?.toLocaleString()}
          </td>
          <td>
            {`${market_share?.high_estimate_pct}%`}
          </td>
        </tr>
      </tbody>
    </table>
  )
}

export default CommodityEstimateTable