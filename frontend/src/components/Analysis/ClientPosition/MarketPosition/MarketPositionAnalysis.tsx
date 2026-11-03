
type MarketPositionAnalysisProps = {
  methodology: string,
  assumptions: string[]
}

const MarketPositionAnalysis = ({ methodology, assumptions }: MarketPositionAnalysisProps) => (
  <div className="flex flex-col gap-2 my-3">

    <h4 className="font-semibold text-teal-100">Analiza tržišne pozicije:</h4>

    <div>
      <p>{methodology}</p>

      <ol className="list-disc [&>li]:text-xs mx-4 my-2">
        {assumptions.map(assumption => (
          <li key={assumption}>{assumption}</li>
        ))}
      </ol>
    </div>
  </div>
)

export default MarketPositionAnalysis
