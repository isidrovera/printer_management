// src/components/ui/label.tsx
import * as React from "react"

interface LabelProps extends React.LabelHTMLAttributes<HTMLLabelElement> {
  className?: string
}

const Label = React.forwardRef<HTMLLabelElement, LabelProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <label
        ref={ref}
        className={`text-sm font-medium leading-none ${className || ''}`}
        {...props}
      >
        {children}
      </label>
    )
  }
)

Label.displayName = "Label"

export { Label }