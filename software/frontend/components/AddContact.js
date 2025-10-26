import React, { useState } from 'react'
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog"
import { Button } from './ui/button'
import { ArrowUpIcon, Settings } from 'lucide-react'
import PhoneInput from 'react-phone-input-2'
import 'react-phone-input-2/lib/style.css'

const AddContact = ({ caretakerNumbers, setCaretakerNumbers }) => {
    const [currentNumber, setCurrentNumber] = useState("")

    const handleAddContact = () => {
        if (!caretakerNumbers.includes(currentNumber)) {
            setCaretakerNumbers([...caretakerNumbers, currentNumber])
            setCurrentNumber("")
        }
    }

    return (
        <Dialog>
            <DialogTrigger asChild>
                <Button variant="outline">
                    Manage Caretaker No. <Settings/>
                </Button>
            </DialogTrigger>
            <DialogContent className="max-w-full sm:max-w-lg w-full">
                <DialogHeader>
                    <DialogTitle>Manage Caretaker No.</DialogTitle>
                </DialogHeader>

                <div className='flex flex-col mt-4 px-4 gap-4'>
                    <div className='flex gap-2 w-full'>
                        <PhoneInput
                            country={'us'}
                            value={currentNumber}
                            onChange={phone => setCurrentNumber(`+${phone}`)}
                            inputStyle={{
                                width: '100%',
                                height: '44px',
                                fontSize: '16px',
                                borderRadius: '0.5rem',
                            }}
                            buttonStyle={{
                                borderRadius: '0.5rem',
                            }}
                            containerStyle={{ flex: 1 }}
                        />
                        <Button
                            variant="outline"
                            size="icon-lg"
                            aria-label="Add"
                            onClick={handleAddContact}
                            className="self-center"
                        >
                            <ArrowUpIcon />
                        </Button>
                    </div>

                    <div className='flex flex-col gap-2 items-center border rounded-lg overflow-y-auto max-h-[40vh] p-2'>
                        {caretakerNumbers.map((item, index) => (
                            <div key={index} className="w-full text-center border-b last:border-b-0 py-1">{item}</div>
                        ))}
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    )
}

export default AddContact