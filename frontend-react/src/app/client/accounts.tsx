import { useEffect, useState } from 'react'
import { ClientLayout } from '@/components/layouts/client-layout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog'
import { accountsAPI, balanceAllocationsAPI } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'
import type { Account, BalanceAllocation } from '@/types/api'
import { CreditCard, Building2, RefreshCw, PieChart, Pencil, Trash2, Plus } from 'lucide-react'

export default function ClientAccounts() {
  const [accounts, setAccounts] = useState<Account[]>([])
  const [externalAccounts, setExternalAccounts] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [loadingExternal, setLoadingExternal] = useState(true)
  const [externalAccountsError, setExternalAccountsError] = useState<string | null>(null)

  // Balance allocations state
  const [balanceAllocations, setBalanceAllocations] = useState<BalanceAllocation[]>([])
  const [loadingAllocations, setLoadingAllocations] = useState(true)
  const [refreshingAllocations, setRefreshingAllocations] = useState(false)
  const [allocationDialogOpen, setAllocationDialogOpen] = useState(false)
  const [editingAllocation, setEditingAllocation] = useState<BalanceAllocation | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [allocationToDelete, setAllocationToDelete] = useState<BalanceAllocation | null>(null)
  const [submittingAllocation, setSubmittingAllocation] = useState(false)
  const [targetShare, setTargetShare] = useState<string>('')

  const { toast } = useToast()

  useEffect(() => {
    const fetchAccounts = async () => {
      try {
        const data = await accountsAPI.getAccounts()
        setAccounts(data)
      } catch (error: any) {
        toast({
          title: 'Ошибка загрузки',
          description: error.response?.data?.detail || 'Не удалось загрузить счета',
          variant: 'destructive',
        })
      } finally {
        setLoading(false)
      }
    }

    fetchAccounts()
  }, [toast])

  useEffect(() => {
    const fetchExternalAccounts = async () => {
      try {
        setExternalAccountsError(null)
        const externalData = await accountsAPI.getExternalAccounts()
        const externalArray = Array.isArray(externalData) ? externalData : []
        setExternalAccounts(externalArray)
        console.log('External accounts loaded:', externalArray.length, 'accounts')
      } catch (error: any) {
        console.error('Failed to load external accounts:', error)
        const errorMessage = error.response?.data?.detail || 'Не удалось загрузить счета из других банков'
        setExternalAccountsError(errorMessage)
        setExternalAccounts([])
      } finally {
        setLoadingExternal(false)
      }
    }

    fetchExternalAccounts()
  }, [])

  const handleRefreshExternalAccounts = async () => {
    setLoadingExternal(true)
    setExternalAccountsError(null)
    try {
      // Invalidate cache and fetch fresh data
      const externalArray = await accountsAPI.getExternalAccountsWithRefresh()
      setExternalAccounts(externalArray)
      console.log('External accounts refreshed:', externalArray.length, 'accounts')
      toast({
        title: 'Обновлено',
        description: `Загружено счетов: ${externalArray.length}`,
      })
    } catch (error: any) {
      console.error('Failed to refresh external accounts:', error)
      const errorMessage = error.response?.data?.detail || 'Не удалось загрузить счета из других банков'
      setExternalAccountsError(errorMessage)
      setExternalAccounts([])
      toast({
        title: 'Ошибка обновления',
        description: errorMessage,
        variant: 'destructive',
      })
    } finally {
      setLoadingExternal(false)
    }
  }

  const handleRefreshBalanceAllocations = async () => {
    setRefreshingAllocations(true)
    try {
      // Invalidate cache and fetch fresh data
      const allocationsArray = await balanceAllocationsAPI.getBalanceAllocationsWithRefresh()
      setBalanceAllocations(allocationsArray)
      console.log('Balance allocations refreshed:', allocationsArray.length, 'allocations')
      toast({
        title: 'Обновлено',
        description: `Загружено распределений: ${allocationsArray.length}`,
      })
    } catch (error: any) {
      console.error('Failed to refresh balance allocations:', error)
      const errorMessage = error.response?.data?.detail || 'Не удалось обновить распределение по банкам'
      toast({
        title: 'Ошибка обновления',
        description: errorMessage,
        variant: 'destructive',
      })
    } finally {
      setRefreshingAllocations(false)
    }
  }

  // Fetch balance allocations
  useEffect(() => {
    const fetchBalanceAllocations = async () => {
      try {
        const data = await balanceAllocationsAPI.getBalanceAllocations()
        setBalanceAllocations(data)
      } catch (error: any) {
        console.error('Failed to load balance allocations:', error)
        toast({
          title: 'Ошибка загрузки',
          description: error.response?.data?.detail || 'Не удалось загрузить распределение по банкам',
          variant: 'destructive',
        })
      } finally {
        setLoadingAllocations(false)
      }
    }

    fetchBalanceAllocations()
  }, [toast])

  const handleOpenAllocationDialog = (allocation: BalanceAllocation | null) => {
    setEditingAllocation(allocation)
    setTargetShare(allocation?.target_share?.toString() || '')
    setAllocationDialogOpen(true)
  }

  // Calculate maximum allowed target share for current allocation
  const getMaxAllowedShare = () => {
    if (!editingAllocation) return 100

    const otherAllocationsTargetSum = balanceAllocations
      .filter(a => a.bank_id !== editingAllocation.bank_id)
      .reduce((sum, a) => {
        const share = a.target_share !== null && a.target_share !== undefined
          ? (typeof a.target_share === 'number' ? a.target_share : parseFloat(a.target_share))
          : 0
        return sum + share
      }, 0)

    return 100 - otherAllocationsTargetSum
  }

  const handleCloseAllocationDialog = () => {
    setAllocationDialogOpen(false)
    setEditingAllocation(null)
    setTargetShare('')
  }

  const handleSaveAllocation = async () => {
    if (!editingAllocation) return

    const targetShareNum = parseFloat(targetShare)
    const maxAllowedShare = getMaxAllowedShare()

    if (isNaN(targetShareNum) || targetShareNum < 0 || targetShareNum > maxAllowedShare) {
      toast({
        title: 'Ошибка валидации',
        description: `Целевая доля должна быть от 0 до ${maxAllowedShare.toFixed(2)}. Сумма всех целевых долей не должна превышать 100%.`,
        variant: 'destructive',
      })
      return
    }

    setSubmittingAllocation(true)
    try {
      if (editingAllocation.id) {
        // Update existing allocation
        const updated = await balanceAllocationsAPI.updateBalanceAllocation(editingAllocation.id, {
          target_share: targetShareNum,
        })
        setBalanceAllocations(balanceAllocations.map(a => a.id === updated.id ? updated : a))
        toast({
          title: 'Успешно',
          description: 'Распределение обновлено',
        })
      } else {
        // Create new allocation
        await balanceAllocationsAPI.createBalanceAllocation({
          bank_id: editingAllocation.bank_id,
          target_share: targetShareNum,
          account_type: 'checking',
        })
        // Refresh allocations to get updated data
        const refreshed = await balanceAllocationsAPI.getBalanceAllocations()
        setBalanceAllocations(refreshed)
        toast({
          title: 'Успешно',
          description: 'Распределение создано',
        })
      }
      handleCloseAllocationDialog()
    } catch (error: any) {
      console.error('Failed to save allocation:', error)
      toast({
        title: 'Ошибка',
        description: error.response?.data?.detail || 'Не удалось сохранить распределение',
        variant: 'destructive',
      })
    } finally {
      setSubmittingAllocation(false)
    }
  }

  const handleOpenDeleteDialog = (allocation: BalanceAllocation) => {
    setAllocationToDelete(allocation)
    setDeleteDialogOpen(true)
  }

  const handleCloseDeleteDialog = () => {
    setDeleteDialogOpen(false)
    setAllocationToDelete(null)
  }

  const handleDeleteAllocation = async () => {
    if (!allocationToDelete || !allocationToDelete.id) return

    try {
      await balanceAllocationsAPI.deleteBalanceAllocation(allocationToDelete.id)
      // Refresh allocations to show bank without target
      const refreshed = await balanceAllocationsAPI.getBalanceAllocations()
      setBalanceAllocations(refreshed)
      toast({
        title: 'Успешно',
        description: 'Распределение удалено',
      })
      handleCloseDeleteDialog()
    } catch (error: any) {
      console.error('Failed to delete allocation:', error)
      toast({
        title: 'Ошибка',
        description: error.response?.data?.detail || 'Не удалось удалить распределение',
        variant: 'destructive',
      })
    }
  }

  return (
    <ClientLayout title="Мои счета">
      <Card className="mb-6">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2">
                <Building2 className="h-5 w-5 text-primary" />
                <CardTitle>Счета Мультибанк</CardTitle>
              </div>
              <CardDescription>Счета из других банков, доступные через OpenBanking</CardDescription>
            </div>
            <button
              onClick={handleRefreshExternalAccounts}
              disabled={loadingExternal}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-primary hover:bg-primary/10 rounded-md transition-colors disabled:opacity-50"
              title="Обновить счета"
            >
              <RefreshCw className={`h-4 w-4 ${loadingExternal ? 'animate-spin' : ''}`} />
              Обновить
            </button>
          </div>
        </CardHeader>
        <CardContent>
          {loadingExternal ? (
            <p className="text-muted-foreground">Загрузка...</p>
          ) : externalAccountsError ? (
            <div className="text-sm text-red-600">
              <p>Ошибка: {externalAccountsError}</p>
            </div>
          ) : externalAccounts.length === 0 ? (
            <p className="text-muted-foreground">
              Нет подключенных счетов из других банков. Добавьте согласие в разделе "Согласия".
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-4 font-medium">Банк</th>
                    <th className="text-left p-4 font-medium">Номер счета</th>
                    <th className="text-left p-4 font-medium">Тип</th>
                    <th className="text-right p-4 font-medium">Баланс</th>
                  </tr>
                </thead>
                <tbody>
                  {externalAccounts.map((acc: any, idx: number) => {
                    const account = acc.account
                    const accountNumber =
                      account?.account && account.account[0]
                        ? account.account[0].identification
                        : 'N/A'
                    const accountType = account?.accountSubType || account?.accountType || 'N/A'
                    const balance = acc.balance
                      ? parseFloat(acc.balance).toLocaleString('ru-RU') + ' ₽'
                      : 'N/A'

                    return (
                      <tr key={idx} className="border-b">
                        <td className="p-4 font-medium">{acc.bank_name || 'N/A'}</td>
                        <td className="p-4 font-mono text-sm">{accountNumber}</td>
                        <td className="p-4">{accountType}</td>
                        <td className="p-4 text-right font-semibold">{balance}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Balance Bank Allocation Section */}
      <Card className="mb-6">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2">
                <PieChart className="h-5 w-5 text-primary" />
                <CardTitle>Распределение по банкам</CardTitle>
              </div>
              <CardDescription>Целевое и фактическое распределение средств по внешним банкам</CardDescription>
            </div>
            <button
              onClick={handleRefreshBalanceAllocations}
              disabled={loadingAllocations || refreshingAllocations}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-primary hover:bg-primary/10 rounded-md transition-colors disabled:opacity-50"
              title="Обновить"
            >
              <RefreshCw className={`h-4 w-4 ${refreshingAllocations ? 'animate-spin' : ''}`} />
              Обновить
            </button>
          </div>
        </CardHeader>
        <CardContent>
          {loadingAllocations || refreshingAllocations ? (
            <p className="text-muted-foreground">Загрузка...</p>
          ) : balanceAllocations.length === 0 ? (
            <p className="text-muted-foreground">
              Нет данных о распределении средств. Добавьте счета из внешних банков.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-4 font-medium">Банк</th>
                    <th className="text-left p-4 font-medium">Тип счета</th>
                    <th className="text-right p-4 font-medium">Целевая доля %</th>
                    <th className="text-right p-4 font-medium">Текущая доля %</th>
                    <th className="text-right p-4 font-medium">Текущая сумма</th>
                    <th className="text-right p-4 font-medium">Действия</th>
                  </tr>
                </thead>
                <tbody>
                  {balanceAllocations.map((allocation, idx) => {
                    const hasTarget = allocation.target_share !== null
                    const actualAmount = parseFloat(allocation.actual_amount || '0')
                    const actualShare = typeof allocation.actual_share === 'number' ? allocation.actual_share : parseFloat(allocation.actual_share || '0')
                    const targetShare = typeof allocation.target_share === 'number' ? allocation.target_share : parseFloat(allocation.target_share || '0')
                    const difference = hasTarget ? actualShare - targetShare : 0
                    const isBalanced = hasTarget && Math.abs(difference) < 1

                    return (
                      <tr key={idx} className="border-b hover:bg-muted/50">
                        <td className="p-4 font-medium">{allocation.bank_name}</td>
                        <td className="p-4">{allocation.account_type}</td>
                        <td className="p-4 text-right">
                          {hasTarget ? (
                            <span className="font-semibold">{targetShare.toFixed(2)}%</span>
                          ) : (
                            <span className="text-muted-foreground">—</span>
                          )}
                        </td>
                        <td className="p-4 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <span className="font-semibold">{actualShare.toFixed(2)}%</span>
                            {hasTarget && (
                              <span className={`text-xs ${
                                isBalanced ? 'text-green-600' :
                                difference > 0 ? 'text-blue-600' : 'text-orange-600'
                              }`}>
                                ({difference > 0 ? '+' : ''}{difference.toFixed(2)}%)
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="p-4 text-right font-semibold">
                          {actualAmount.toLocaleString('ru-RU')} ₽
                        </td>
                        <td className="p-4 text-right">
                          <div className="flex justify-end gap-2">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleOpenAllocationDialog(allocation)}
                            >
                              {hasTarget ? (
                                <>
                                  <Pencil className="h-3 w-3 mr-1" />
                                  Изменить
                                </>
                              ) : (
                                <>
                                  <Plus className="h-3 w-3 mr-1" />
                                  Задать цель
                                </>
                              )}
                            </Button>
                            {hasTarget && allocation.id && (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleOpenDeleteDialog(allocation)}
                              >
                                <Trash2 className="h-3 w-3" />
                              </Button>
                            )}
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Allocation Dialog */}
      <Dialog open={allocationDialogOpen} onOpenChange={setAllocationDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {editingAllocation?.id ? 'Изменить распределение' : 'Задать целевое распределение'}
            </DialogTitle>
            <DialogDescription>
              Установите целевую долю для банка {editingAllocation?.bank_name}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="bank_name">Банк</Label>
              <Input
                id="bank_name"
                value={editingAllocation?.bank_name || ''}
                disabled
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="account_type">Тип счета</Label>
              <Input
                id="account_type"
                value={editingAllocation?.account_type || 'checking'}
                disabled
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="target_share">Целевая доля (%)</Label>
              <Input
                id="target_share"
                type="number"
                min="0"
                max={getMaxAllowedShare()}
                step="0.01"
                value={targetShare}
                onChange={(e) => setTargetShare(e.target.value)}
                placeholder={`Введите процент (0-${getMaxAllowedShare().toFixed(2)})`}
              />
              <p className="text-sm text-muted-foreground">
                Максимальная доля: {getMaxAllowedShare().toFixed(2)}% (осталось от 100%)
              </p>
            </div>
            {editingAllocation && (
              <div className="grid gap-2">
                <Label>Текущие показатели</Label>
                <div className="text-sm space-y-1">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Текущая доля:</span>
                    <span className="font-semibold">
                      {(typeof editingAllocation.actual_share === 'number'
                        ? editingAllocation.actual_share
                        : parseFloat(editingAllocation.actual_share || '0')).toFixed(2)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Текущая сумма:</span>
                    <span className="font-semibold">
                      {parseFloat(editingAllocation.actual_amount).toLocaleString('ru-RU')} ₽
                    </span>
                  </div>
                  <div className="flex justify-between pt-2 border-t">
                    <span className="text-muted-foreground">Сумма целевых долей других банков:</span>
                    <span className="font-semibold">
                      {(100 - getMaxAllowedShare()).toFixed(2)}%
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={handleCloseAllocationDialog}>
              Отмена
            </Button>
            <Button onClick={handleSaveAllocation} disabled={submittingAllocation}>
              {submittingAllocation ? 'Сохранение...' : 'Сохранить'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Удалить целевое распределение?</AlertDialogTitle>
            <AlertDialogDescription>
              Вы уверены, что хотите удалить целевое распределение для банка {allocationToDelete?.bank_name}?
              Это действие нельзя отменить.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={handleCloseDeleteDialog}>Отмена</AlertDialogCancel>
            <AlertDialogAction onClick={handleDeleteAllocation}>Удалить</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {loading ? (
        <p className="text-muted-foreground">Загрузка...</p>
      ) : accounts.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <p className="text-center text-muted-foreground">У вас нет счетов</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {accounts.map((account) => (
            <Card key={account.account_id}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CreditCard className="h-8 w-8 text-primary" />
                  <span className={`px-2 py-1 text-xs rounded ${
                    account.status === 'active' 
                      ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                      : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
                  }`}>
                    {account.status}
                  </span>
                </div>
                <CardTitle className="text-lg mt-4">{account.account_number}</CardTitle>
                <CardDescription>{account.account_type}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Баланс:</span>
                    <span className="font-bold text-lg">
                      {account.balance.toLocaleString('ru-RU')} {account.currency}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Банк:</span>
                    <span className="text-sm">{account.bank_code}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </ClientLayout>
  )
}

