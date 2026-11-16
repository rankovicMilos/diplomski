import NewAnalysisForm from "@/src/components/Analysis/NewAnalysis/NewAnalysisForm";

const NewPeerAnalysis = () => {

  return (
    <div className="flex flex-col gap-6 max-w-[880px] lg:pr-6">
      <div className="flex flex-col gap-2">
        <span className="text-2xs font-semibold uppercase tracking-[0.18em] text-teal-100">Novi izveštaj</span>
        <h1>Generisanje UAF obrasca</h1>
      </div>
      <div className="flex flex-col gap-6 glass rounded-md p-5 md:p-8">
        <NewAnalysisForm />
      </div>
    </div>
  )
}

export default NewPeerAnalysis;