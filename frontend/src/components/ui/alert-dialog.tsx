// src/components/ui/alert-dialog.tsx
import * as React from "react"
import * as AlertDialogPrimitive from "@radix-ui/react-alert-dialog"
import { cn } from "@/lib/utils"

// Componentes base
const AlertDialog = AlertDialogPrimitive.Root
const AlertDialogTrigger = AlertDialogPrimitive.Trigger
const AlertDialogPortal = AlertDialogPrimitive.Portal

// Overlay component
const AlertDialogOverlay = React.forwardRef<any, any>(
  (props, ref) => (
    <AlertDialogPrimitive.Overlay
      className="fixed inset-0 z-50 bg-black/50"
      {...props}
      ref={ref}
    />
  )
)

// Content component
const AlertDialogContent = React.forwardRef<any, any>(
  (props, ref) => (
    <AlertDialogPortal>
      <AlertDialogOverlay />
      <AlertDialogPrimitive.Content
        ref={ref}
        className={cn(
          "fixed left-1/2 top-1/2 z-50 -translate-x-1/2 -translate-y-1/2 bg-white p-6 shadow-lg rounded-lg",
          props.className
        )}
        {...props}
      />
    </AlertDialogPortal>
  )
)

// Title component
const AlertDialogTitle = React.forwardRef<any, any>(
  (props, ref) => (
    <AlertDialogPrimitive.Title
      ref={ref}
      className={cn("text-lg font-semibold", props.className)}
      {...props}
    />
  )
)

// Description component
const AlertDialogDescription = React.forwardRef<any, any>(
  (props, ref) => (
    <AlertDialogPrimitive.Description
      ref={ref}
      className={cn("text-sm text-gray-500", props.className)}
      {...props}
    />
  )
)

// Action component
const AlertDialogAction = React.forwardRef<any, any>(
  (props, ref) => (
    <AlertDialogPrimitive.Action
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center px-4 py-2 font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700",
        props.className
      )}
      {...props}
    />
  )
)

// Cancel component
const AlertDialogCancel = React.forwardRef<any, any>(
  (props, ref) => (
    <AlertDialogPrimitive.Cancel
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center px-4 py-2 font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200",
        props.className
      )}
      {...props}
    />
  )
)

// Set display names
AlertDialogOverlay.displayName = "AlertDialogOverlay"
AlertDialogContent.displayName = "AlertDialogContent"
AlertDialogTitle.displayName = "AlertDialogTitle"
AlertDialogDescription.displayName = "AlertDialogDescription"
AlertDialogAction.displayName = "AlertDialogAction"
AlertDialogCancel.displayName = "AlertDialogCancel"

export {
  AlertDialog,
  AlertDialogTrigger,
  AlertDialogContent,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogAction,
  AlertDialogCancel
}