import capitalizeWords from "@/src/utils/helpers/capitalizeWords"

type PeerRankingsProps = {
  peerRankings: {
    by_total_assets: string[],
    by_total_revenue: string[],
    by_operating_margin: string[]
  }
}

const PeerRankings = ({ peerRankings }: PeerRankingsProps) => {

  return (
    <div className="flex flex-col gap-4">
      <h4 className="font-semibold text-teal-100">Rang lista preduzeća</h4>

      {Object.entries(peerRankings).map(([key, ranking]) => (
        <div key={key}>
          <h5 className="font-semibold">{capitalizeWords(key.replaceAll("_", " "))}:</h5>
          <ol className="list-decimal ml-10">
            {ranking.map(ranking => <li key={ranking}>{capitalizeWords(ranking)}</li>)}
          </ol>
        </div>
      ))
      }

    </div>
  )
}

export default PeerRankings;