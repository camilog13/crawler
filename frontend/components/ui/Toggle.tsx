"use client";

import * as Switch from "@radix-ui/react-switch";

export default function Toggle({
  checked,
  onChange
}: {
  checked: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <Switch.Root
      className="w-10 h-5 bg-slate-700 rounded-full relative data-[state=checked]:bg-emerald-500 outline-none cursor-pointer"
      checked={checked}
      onCheckedChange={onChange}
    >
      <Switch.Thumb className="block w-4 h-4 bg-white rounded-full shadow transform translate-x-0.5 data-[state=checked]:translate-x-[18px] transition-transform" />
    </Switch.Root>
  );
}
