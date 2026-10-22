import NewAnalysisForm from "@/src/components/Analysis/NewAnalysis/NewAnalysisForm";

const NewPeerAnalysis = () => {

  return (
    <div className="flex flex-col gap-5">
      <h1>Generate UAF (User Acceptance Form)</h1>
      <NewAnalysisForm />

    </div>
  )
}

export default NewPeerAnalysis;