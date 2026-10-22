import { groupBy } from "@/src/utils/helpers/groupBy"
import { LineChart } from "@mui/x-charts"

type LineChartDisplayProps = {
  title?: string,
  data: {
    label: string,
    value: number
  }[]
}

const LineChartDisplay = ({ title, data }: LineChartDisplayProps) => {
  /**
   * Prerequisites:
   *  - Data label is always in format 'crop year'
   * 
   * Data for series is grouped by crop name from data label
   * Data for xAxis is taken from unique years from data labels
   * 
   */

  const xAxisData = [...new Set(data.map(item => item.label.split(' ')[1]))]

  const groupedContent = groupBy(data, (dataItem) => (dataItem.label.split(' ')[0]));

  return (
    <div>
      {title &&
        <h5 className="text-xs text-teal-100 font-semibold">{title}:</h5>
      }

      <LineChart
        xAxis={[{ scaleType: "point", data: xAxisData }]}
        series={Object.entries(groupedContent).map(([label, values]) => ({
          label: label,
          data: values.map(val => val.value)
        }))}
        height={450}
      />
    </div>
  )

}

export default LineChartDisplay