import { groupBy } from "@/src/utils/helpers/groupBy"
import { BarChart } from "@mui/x-charts"

type BarChartDisplayProps = {
  title: string,
  data: {
    label: string,
    value: number
  }[]
}

const BarChartDisplay = ({ title, data }: BarChartDisplayProps) => {
  /**
   * Prerequisites:
   *  - Data label is always in format 'crop year'
   * 
   * Data for series is grouped by year from data label
   * Data for xAxis is taken from unique crop names from data labels
   * 
   */

  const xAxisData = [...new Set(data.map(item => item.label.split(" ")[0]))]

  const groupedContent = groupBy(data, (dataItem) => (dataItem.label.split(' ')[1]));


  return (
    <div>
      <h5 className="text-xs text-teal-100 font-semibold">{title}:</h5>
      <BarChart
        xAxis={[{ scaleType: 'band', data: xAxisData, categoryGapRatio: 0.4, barGapRatio: 0.15 }]}
        yAxis={[{ label: 'Price', min: 0 }]}
        series={Object.entries(groupedContent).map(([year, values]) => ({ data: values.map(v => v.value), label: year }))}
        height={300}
      />
    </div>
  )

}

export default BarChartDisplay