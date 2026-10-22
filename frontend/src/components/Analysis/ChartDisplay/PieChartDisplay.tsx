import { PieChart } from "@mui/x-charts"

type PieChartDisplayProps = {
  title: string,
  data: {
    label: string,
    value: number
  }[]
}

const PieChartDisplay = ({ title, data }: PieChartDisplayProps) => {
  return (
    <div>
      <h5 className="text-xs text-teal-100 font-semibold">{title}:</h5>

      <PieChart
        series={[{ data: data }]}
        width={200}
        height={200}
      />
    </div>
  )

}

export default PieChartDisplay