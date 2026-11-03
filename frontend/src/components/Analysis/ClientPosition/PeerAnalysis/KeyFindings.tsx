type KeyFindingsProps = {
  findings: {
    finding: string,
    companies_affected: string[],
    significance: string
  }[]
}

const KeyFindings = ({ findings }: KeyFindingsProps) => {
  return (
    <div className="flex flex-col gap-4">

      <h4 className="font-semibold text-teal-100">Ključni nalazi uporedne analize:</h4>

      <ul className="flex flex-col gap-5">
        {findings.map((finding, index) => (
          <li key={`finding-${index}`} className="flex flex-col">
            <p className="text-teal-100 font-bold">Nalaz {index + 1} ({finding.significance}):</p>
            <span className="text-xs text-center">{finding.finding}</span>
            <span className="text-charcoal-50 text-2xs text-center">Obuhvaćena preduzeća: {finding.companies_affected.join(", ")}</span>
          </li>
        ))}
      </ul>


    </div>
  )


}

export default KeyFindings;