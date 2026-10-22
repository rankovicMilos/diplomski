import { groupBy } from "@/src/utils/helpers/groupBy"
import { LineChart } from "@mui/x-charts"
import { Fragment } from "react/jsx-runtime"

type MarketAnalysisTableProps = {
  table: {
    id: string,
    title: string,
    columns: {
      id: string,
      name: string,
      type: string
    }[],
    rows: (string | number | null)[][]
  } | undefined
}

const MarketAnalysisTable = ({ table }: MarketAnalysisTableProps) => {

  if (!table) return;

  if (table.id === "production_stats") {
    const columns = table.columns.filter(col => col.id !== "crop" && col.id !== "year")

    const groupedCrops = groupBy(table.rows, (row) => row[0] || "")
    const rows = Object.entries(groupedCrops).map(([key, crops]) => [key, ...crops.map(crop => crop.slice(2)).flat()])
    const years = [...new Set(table.rows.map(row => row[1]))]
    return (
      <table className='my-2'>
        <caption className="text-start text-xs">{table.title}</caption>
        <thead>
          <tr className="bg-teal-90 text-sm">
            <th rowSpan={2} className="align-bottom">
              Crop
            </th>
            {years.map(year =>
              (<th key={year} colSpan={3}>{year}</th>)
            )}
          </tr>
          <tr className="bg-teal-40">
            {years.map((year) => (
              <Fragment key={year}>
                {
                  columns.map((col) => (
                    <th key={`${col.id}-1`} className="font-medium">{col.name}</th>
                  ))
                }
              </Fragment>

            ))}

          </tr>
        </thead>
        <tbody className="text-xs even:[&>tr]:bg-teal-10">
          {rows.map((row, index) => (
            <tr key={`row-index-${index}`}>
              {row.map((item, cellIndex) => (
                <td key={`item-${index}-${cellIndex}`} className="tabular-nums">{item?.toLocaleString()}</td>
              ))}
            </tr>
          ))}

        </tbody>
      </table>
    )
  }

  if (table.id === "price_history") {
    const values = table.rows.map(item => ({ label: `${item[0]} ${item[1]?.toString()?.replace(" ", "_")}`, value: Number(item[2]) || 0 }))

    const parseDate = (dateStr: string) => {
      const [month, year] = dateStr.split('_')
      const monthIndex = new Date(`${month} 1, 2000`).getMonth()
      return new Date(parseInt(year), monthIndex, 1).getTime()
    }

    const xAxisData = [...new Set(values.map(item => item.label.split(' ')[1]))]
      .sort((a, b) => parseDate(a) - parseDate(b))

    const groupedContent = groupBy(values, (dataItem) => dataItem.label.split(' ')[0])

    const series = Object.entries(groupedContent).map(([label, items]) => {
      const valueMap = new Map(items.map(v => [v.label.split(' ')[1], v.value]))
      return {
        label: label,
        data: xAxisData.map(x => valueMap.get(x) ?? null),
        connectNulls: true
      }
    })

    return (
      <div className='my-2'>
        <p className="text-start text-xs">{table.title}</p>
        <LineChart
          xAxis={[{ scaleType: "point", data: xAxisData }]}
          series={series}
          height={450}
        />
      </div>
    )
  }

  return (
    <table className='w-[80%] my-2'>
      <caption className="text-start text-xs">{table.title}</caption>
      <thead className="bg-teal-40 font-bold text-sm">
        <tr>
          {table.columns.map((col) => (
            <th key={col.id}>{col.name}</th>
          ))}
        </tr>
      </thead>
      <tbody className="text-xs even:[&>tr]:bg-teal-10">
        {table.rows.map((row, index) => (
          <tr key={`row-index-${index}`}>
            {row.map((item, cellIndex) => (
              <td key={`item-${index}-${cellIndex}`}>{item?.toLocaleString()}</td>
            ))}
          </tr>
        ))}

      </tbody>
    </table>
  )
}

export default MarketAnalysisTable;