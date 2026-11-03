'use client'
import { TextField } from "@mui/material"
import { useQueryState } from "nuqs"
import { FormEvent, useState } from "react"

const SearchByClient = () => {
  const [clientName, setClientName] = useQueryState("clientName", { defaultValue: "" })
  const [clientNameState, setClientNameState] = useState<string>(clientName)

  const onSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setClientName(clientNameState)
  }

  return (
    <form onSubmit={onSubmit}>
      <TextField value={clientNameState} onChange={e => setClientNameState(e.target.value)} size="small" label="Naziv klijenta" />
    </form>
  )
}

export default SearchByClient