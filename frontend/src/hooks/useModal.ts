import { useCallback, useState } from 'react'

/**
 * モーダル管理用カスタムフック
 *
 * @returns [isOpen, open, close] - モーダルの開閉状態と操作関数
 *
 * @example
 * const [buyModalOpen, openBuyModal, closeBuyModal] = useModal()
 */
export function useModal(): [boolean, () => void, () => void] {
  const [isOpen, setIsOpen] = useState(false)

  const open = useCallback(() => {
    setIsOpen(true)
  }, [])

  const close = useCallback(() => {
    setIsOpen(false)
  }, [])

  return [isOpen, open, close]
}
