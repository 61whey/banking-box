import { useEffect, useState } from 'react'
import { ClientLayout } from '@/components/layouts/client-layout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Skeleton } from '@/components/ui/skeleton'
import { virtualAccountsAPI } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'
import type { VirtualAccount, VirtualAccountCreate, VirtualAccountUpdate, AccountType, CalculationType } from '@/types/api'
import { Plus, Edit2, Trash2, Wallet } from 'lucide-react'

export default function VirtualAccounts() {
  const [accounts, setAccounts] = useState<VirtualAccount[]>([])
  const [loading, setLoading] = useState(true)
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [selectedAccount, setSelectedAccount] = useState<VirtualAccount | null>(null)
  const [submitting, setSubmitting] = useState(false)

  // Form state
  const [formData, setFormData] = useState<VirtualAccountCreate>({
    account_type: 'checking',
    calculation_type: 'automatic',
    balance: undefined,
    currency: 'RUB'
  })

  const { toast } = useToast()

  const fetchAccounts = async () => {
    try {
      setLoading(true)
      const data = await virtualAccountsAPI.getVirtualAccounts()
      setAccounts(data)
    } catch (error: any) {
      toast({
        title: 'Ошибка загрузки',
        description: error.response?.data?.detail || 'Не удалось загрузить виртуальные счета',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAccounts()
  }, [])

  const handleCreateOpen = () => {
    setFormData({
      account_type: 'checking',
      calculation_type: 'automatic',
      balance: undefined,
      currency: 'RUB'
    })
    setCreateDialogOpen(true)
  }

  const handleEditOpen = (account: VirtualAccount) => {
    setSelectedAccount(account)
    setFormData({
      account_type: account.account_type,
      calculation_type: account.calculation_type,
      balance: account.calculation_type === 'fixed' ? account.balance : undefined,
      currency: account.currency
    })
    setEditDialogOpen(true)
  }

  const handleDeleteOpen = (account: VirtualAccount) => {
    setSelectedAccount(account)
    setDeleteDialogOpen(true)
  }

  const handleCreate = async () => {
    try {
      setSubmitting(true)
      await virtualAccountsAPI.createVirtualAccount(formData)
      toast({
        title: 'Успешно',
        description: 'Виртуальный счет создан',
      })
      setCreateDialogOpen(false)
      fetchAccounts()
    } catch (error: any) {
      toast({
        title: 'Ошибка создания',
        description: error.response?.data?.detail || 'Не удалось создать виртуальный счет',
        variant: 'destructive',
      })
    } finally {
      setSubmitting(false)
    }
  }

  const handleUpdate = async () => {
    if (!selectedAccount) return

    try {
      setSubmitting(true)
      const updateData: VirtualAccountUpdate = {
        account_type: formData.account_type,
        calculation_type: formData.calculation_type,
        balance: formData.calculation_type === 'fixed' ? formData.balance : undefined,
        currency: formData.currency
      }
      await virtualAccountsAPI.updateVirtualAccount(selectedAccount.id, updateData)
      toast({
        title: 'Успешно',
        description: 'Виртуальный счет обновлен',
      })
      setEditDialogOpen(false)
      setSelectedAccount(null)
      fetchAccounts()
    } catch (error: any) {
      toast({
        title: 'Ошибка обновления',
        description: error.response?.data?.detail || 'Не удалось обновить виртуальный счет',
        variant: 'destructive',
      })
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async () => {
    if (!selectedAccount) return

    try {
      setSubmitting(true)
      await virtualAccountsAPI.deleteVirtualAccount(selectedAccount.id)
      toast({
        title: 'Успешно',
        description: 'Виртуальный счет удален',
      })
      setDeleteDialogOpen(false)
      setSelectedAccount(null)
      fetchAccounts()
    } catch (error: any) {
      toast({
        title: 'Ошибка удаления',
        description: error.response?.data?.detail || 'Не удалось удалить виртуальный счет',
        variant: 'destructive',
      })
    } finally {
      setSubmitting(false)
    }
  }

  const getAccountTypeLabel = (type: string) => {
    switch (type) {
      case 'checking': return 'Расчетный'
      case 'savings': return 'Сберегательный'
      default: return type
    }
  }

  const getCalculationTypeLabel = (type: string) => {
    switch (type) {
      case 'automatic': return 'Автоматический'
      case 'fixed': return 'Фиксированный'
      default: return type
    }
  }

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'active': return 'Активен'
      case 'inactive': return 'Неактивен'
      case 'closed': return 'Закрыт'
      default: return status
    }
  }

  const formatBalance = (balance: string) => {
    const num = parseFloat(balance)
    return num.toLocaleString('ru-RU', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  }

  return (
    <ClientLayout title="Виртуальные счета">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2">
                <Wallet className="h-5 w-5 text-primary" />
                <CardTitle>Виртуальные счета</CardTitle>
              </div>
              <CardDescription>
                Управление виртуальными счетами для распределения средств
              </CardDescription>
            </div>
            <Button onClick={handleCreateOpen}>
              <Plus className="mr-2 h-4 w-4" />
              Создать счет
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-2">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : accounts.length === 0 ? (
            <div className="text-center py-12">
              <Wallet className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium mb-2">Нет виртуальных счетов</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Создайте первый виртуальный счет для начала работы
              </p>
              <Button onClick={handleCreateOpen}>
                <Plus className="mr-2 h-4 w-4" />
                Создать счет
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Номер счета</TableHead>
                  <TableHead>Тип</TableHead>
                  <TableHead>Расчет</TableHead>
                  <TableHead>Баланс</TableHead>
                  <TableHead>Валюта</TableHead>
                  <TableHead>Статус</TableHead>
                  <TableHead className="text-right">Действия</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {accounts.map((account) => (
                  <TableRow key={account.id}>
                    <TableCell className="font-mono">{account.account_number}</TableCell>
                    <TableCell>{getAccountTypeLabel(account.account_type)}</TableCell>
                    <TableCell>{getCalculationTypeLabel(account.calculation_type)}</TableCell>
                    <TableCell className="font-mono">{formatBalance(account.balance)}</TableCell>
                    <TableCell>{account.currency}</TableCell>
                    <TableCell>
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        account.status === 'active' ? 'bg-green-100 text-green-800' :
                        account.status === 'inactive' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {getStatusLabel(account.status)}
                      </span>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleEditOpen(account)}
                        >
                          <Edit2 className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDeleteOpen(account)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Create Dialog */}
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Создать виртуальный счет</DialogTitle>
            <DialogDescription>
              Номер счета будет сгенерирован автоматически
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="create-account-type">Тип счета</Label>
              <Select
                value={formData.account_type}
                onValueChange={(value) => setFormData({ ...formData, account_type: value })}
              >
                <SelectTrigger id="create-account-type">
                  <SelectValue placeholder="Выберите тип счета" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="checking">Расчетный</SelectItem>
                  <SelectItem value="savings">Сберегательный</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="create-calculation-type">Тип расчета</Label>
              <Select
                value={formData.calculation_type}
                onValueChange={(value) => {
                  setFormData({
                    ...formData,
                    calculation_type: value,
                    balance: value === 'automatic' ? undefined : formData.balance
                  })
                }}
              >
                <SelectTrigger id="create-calculation-type">
                  <SelectValue placeholder="Выберите тип расчета" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="automatic">Автоматический</SelectItem>
                  <SelectItem value="fixed">Фиксированный</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {formData.calculation_type === 'fixed' && (
              <div className="grid gap-2">
                <Label htmlFor="create-balance">Баланс</Label>
                <Input
                  id="create-balance"
                  type="number"
                  step="0.01"
                  placeholder="0.00"
                  value={formData.balance || ''}
                  onChange={(e) => setFormData({ ...formData, balance: e.target.value })}
                />
              </div>
            )}

            <div className="grid gap-2">
              <Label htmlFor="create-currency">Валюта</Label>
              <Select
                value={formData.currency}
                onValueChange={(value) => setFormData({ ...formData, currency: value })}
              >
                <SelectTrigger id="create-currency">
                  <SelectValue placeholder="Выберите валюту" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="RUB">RUB</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateDialogOpen(false)} disabled={submitting}>
              Отмена
            </Button>
            <Button onClick={handleCreate} disabled={submitting}>
              {submitting ? 'Создание...' : 'Создать'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Редактировать виртуальный счет</DialogTitle>
            <DialogDescription>
              Счет: {selectedAccount?.account_number}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="edit-account-type">Тип счета</Label>
              <Select
                value={formData.account_type}
                onValueChange={(value) => setFormData({ ...formData, account_type: value })}
              >
                <SelectTrigger id="edit-account-type">
                  <SelectValue placeholder="Выберите тип счета" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="checking">Расчетный</SelectItem>
                  <SelectItem value="savings">Сберегательный</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="edit-calculation-type">Тип расчета</Label>
              <Select
                value={formData.calculation_type}
                onValueChange={(value) => {
                  setFormData({
                    ...formData,
                    calculation_type: value,
                    balance: value === 'automatic' ? undefined : formData.balance
                  })
                }}
              >
                <SelectTrigger id="edit-calculation-type">
                  <SelectValue placeholder="Выберите тип расчета" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="automatic">Автоматический</SelectItem>
                  <SelectItem value="fixed">Фиксированный</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {formData.calculation_type === 'fixed' && (
              <div className="grid gap-2">
                <Label htmlFor="edit-balance">Баланс</Label>
                <Input
                  id="edit-balance"
                  type="number"
                  step="0.01"
                  placeholder="0.00"
                  value={formData.balance || ''}
                  onChange={(e) => setFormData({ ...formData, balance: e.target.value })}
                />
              </div>
            )}

            <div className="grid gap-2">
              <Label htmlFor="edit-currency">Валюта</Label>
              <Select
                value={formData.currency}
                onValueChange={(value) => setFormData({ ...formData, currency: value })}
              >
                <SelectTrigger id="edit-currency">
                  <SelectValue placeholder="Выберите валюту" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="RUB">RUB</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditDialogOpen(false)} disabled={submitting}>
              Отмена
            </Button>
            <Button onClick={handleUpdate} disabled={submitting}>
              {submitting ? 'Сохранение...' : 'Сохранить'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Удалить виртуальный счет?</AlertDialogTitle>
            <AlertDialogDescription>
              Вы уверены, что хотите удалить счет {selectedAccount?.account_number}? Это действие нельзя отменить.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={submitting}>Отмена</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} disabled={submitting}>
              {submitting ? 'Удаление...' : 'Удалить'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </ClientLayout>
  )
}
