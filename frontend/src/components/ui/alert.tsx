// src/components/ui/alert.tsx
import * as React from "react"
import { cn } from "@/lib/utils"
import { AlertCircle } from "lucide-react"

interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
 variant?: "default" | "destructive"
}

const Alert = React.forwardRef<HTMLDivElement, AlertProps>(
 ({ className, variant = "default", ...props }, ref) => (
   <div
     ref={ref}
     role="alert"
     className={cn(
       "relative w-full rounded-lg border p-4",
       {
         "bg-background text-foreground": variant === "default",
         "bg-destructive/15 text-destructive border-destructive/50": variant === "destructive",
       },
       className
     )}
     {...props}
   />
 )
)
Alert.displayName = "Alert"

const AlertTitle = React.forwardRef
 HTMLParagraphElement,
 React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
 <h5
   ref={ref}
   className={cn("mb-1 font-medium leading-none tracking-tight", className)}
   {...props}
 />
))
AlertTitle.displayName = "AlertTitle"

const AlertDescription = React.forwardRef
 HTMLParagraphElement,
 React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
 <div
   ref={ref}
   className={cn("text-sm [&_p]:leading-relaxed", className)}
   {...props}
 />
))
AlertDescription.displayName = "AlertDescription"

export { Alert, AlertTitle, AlertDescription }